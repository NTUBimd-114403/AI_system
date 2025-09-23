from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import random, json, re, uuid, os, traceback
from datetime import datetime

# ===== App & CORS =====
app = FastAPI(title="TOEIC Part 3 Generator API (OpenAI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ===== Config =====
CHROMA_PATH = "/app/chroma_db"
JSONL_PATH  = "/app/json/toeic_part3_db_ready.jsonl"

OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")   # 與 part2 一致的用法
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")                # 必填

# ===== OpenAI Client =====
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== Embedding & Chroma =====
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client   = chromadb.PersistentClient(path=CHROMA_PATH)
collection           = chroma_client.get_collection("toeic_part3")
scenario_collection  = chroma_client.get_collection("toeic_scenarios")

# ===== Schema（跟 part2 同風格，但為 Part 3、三題、A~D）=====
PART3_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["toeic_listeningmaterial", "toeic_questions"],
    "properties": {
        "toeic_listeningmaterial": {
            "type": "object",
            "additionalProperties": False,
            "required": ["audio_url", "transcript", "accent", "topic", "speaker_count", "listening_level"],
            "properties": {
                "audio_url": {"type": ["string","null"]},
                "transcript": {"type": "string"},
                "accent": {"type": "string"},
                "topic": {"type": "string"},
                "speaker_count": {"type": "string"},                            # "2" 或 "3"
                "listening_level": {"enum": ["beginner","intermediate","advanced"]},
            }
        },
        "toeic_questions": {
            "type": "array",
            "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["question_text","question_type","question_category","passage_id",
                             "question_image_url","part","option_a_text","option_b_text","option_c_text",
                             "option_d_text","is_correct","difficulty_level","explanation"],
                "properties": {
                    "question_text": {"type": "string"},
                    "question_type": {"type": "string", "enum": ["listen"]},
                    "question_category": {"type": "string", "enum": ["pos", "tense", "syntax", "vocab"]},
                    "passage_id": {"type": ["string","null"]},
                    "question_image_url": {"type": ["string","null"]},
                    "part": {"type": "string","enum": ["3"]},
                    "option_a_text": {"type": "string"},
                    "option_b_text": {"type": "string"},
                    "option_c_text": {"type": "string"},
                    "option_d_text": {"type": "string"},
                    "is_correct": {"enum": ["A","B","C","D"]},
                    "difficulty_level": {"enum":["1","2","3","4","5"]},
                    "explanation": {"type": "string"}   # 繁中說明
                }
            }
        }
    }
}

# ===== Utils =====
class GenerateRequest(BaseModel):
    query_text: str = "Part 3 TOEIC listening conversation with 3 questions"

def clean_text(s: str) -> str:
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', s)

def generate_uuid() -> str:
    return str(uuid.uuid4())

@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "model": OPENAI_MODEL,
        "has_api_key": bool(OPENAI_API_KEY),
    }

# ===== 核心路由（與 part2 相同風格）=====
@app.post("/generate_part3")
def generate_part3(req: GenerateRequest):
    try:
        # 1) 隨機挑情境
        scenario_keywords = ["企業發展","外食","娛樂","金融／預算","一般商務","保健",
                             "房屋／公司地產","製造業","辦公室","人事","採購","技術層面","旅遊"]
        scenario_text = random.choice(scenario_keywords)

        # 2) 檢索相似對話/題型 & 情境示例
        query_embedding = embedding_model.encode(req.query_text).tolist()
        res_q = collection.query(query_embeddings=[query_embedding], n_results=3)
        similar = res_q.get("documents") and res_q["documents"][0] or []
        sample_ctx = f"Example: {similar[0][:500]}..." if similar else "Example: (no similar found)"

        scenario_embedding = embedding_model.encode(scenario_text).tolist()
        res_s = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
        scenario_context = res_s.get("documents") and res_s["documents"][0][0] or scenario_text

        # 3) Prompt（注意：transcript 開頭必須固定句；explanation 用繁中）
        prompt = f"""
你是一位專業 TOEIC 出題專家。根據下列測驗情境與範例題目，生成一組 TOEIC Part 3 聽力題組（**只輸出 JSON，且符合指定 Schema**）：

### 測驗情境：
{scenario_context}

### 範例題目（僅供風格參考，勿抄）：
{sample_ctx}

製作要點：
- 先產生一段 **雙/三人對話**（3–5 句；總長約 80–120 字；平均每句 15–25 字）。
- **transcript** 必須以這句開頭：
  "Questions 1 through 3. Refer to the following conversation."
  然後立刻接續對話內容；行與行之間用文字 "\\n" 表示換行。
- 生成 **3 題**；每題 **選項 A~D**；`part` 為 "3"。
- **explanation** 用繁體中文，指出文法重點或語意差異，不可空泛。
- 其他內容一律英文；**topic** 請使用：{scenario_text}
- 嚴格遵守 JSON Schema，不要輸出多餘欄位。
""".strip()

        # 4) 呼叫 OpenAI（與 part2 同風格：Chat Completions + json_schema）
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "toeic_part3",
                    "schema": PART3_JSON_SCHEMA,
                    "strict": True
                }
            }
        )

        raw_output = resp.choices[0].message.content
        cleaned_output = clean_text(raw_output or "")

        # 5) 解析 JSON
        try:
            data = json.loads(cleaned_output)
            parsing_success = True
        except Exception:
            data = {"raw_output": cleaned_output}
            parsing_success = False

        # 6) 解析成功才補 UUID 並寫入 JSONL
        if parsing_success and "toeic_listeningmaterial" in data:
            material_id = generate_uuid()
            data["toeic_listeningmaterial"]["material_id"] = material_id
            for q in data.get("toeic_questions", []):
                q["question_id"] = generate_uuid()
                q["material_id"] = material_id

            os.makedirs(os.path.dirname(JSONL_PATH), exist_ok=True)
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        # 7) 回傳
        return {"success": parsing_success, "data": data}

    except Exception:
        # 與 part2 相同風格：直接回傳 traceback 方便你現在除錯
        raise HTTPException(status_code=500, detail=traceback.format_exc())

if __name__ == "__main__":
    import uvicorn
    # 建議用固定內部埠 8001，讓 docker-compose 對映 11433:8001
    uvicorn.run("part3_api:app", host="0.0.0.0", port=8001, reload=True, log_level="debug")
