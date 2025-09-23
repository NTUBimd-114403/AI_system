# part6_api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import random, json, re, uuid, os, traceback
from datetime import datetime

# ===== App & CORS =====
app = FastAPI(title="TOEIC Part 6 Generator API (OpenAI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ===== Config =====
CHROMA_PATH = "/app/chroma_db"
JSONL_PATH  = "/app/json/toeic_part6_db_ready.jsonl"

OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

# ===== OpenAI Client =====
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== Embedding & Chroma =====
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client   = chromadb.PersistentClient(path=CHROMA_PATH)
collection           = chroma_client.get_collection("toeic_part6")
scenario_collection  = chroma_client.get_collection("toeic_scenarios")

# ===== Schema (Part 6 專用) =====
TOEIC_PART6_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reading_passage", "questions"],
    "properties": {
        "reading_passage": {
            "type": "object",
            "additionalProperties": False,
            "required": ["topic", "title", "reading_level", "content", "word_count", "created_at", "updated_at", "is_approved", "rejection_reason"],
            "properties": {
                "topic": {"type": "string"},
                "title": {"type": "string"},
                "reading_level": {"enum": ["beginner","intermediate","advanced"]},
                "content": {"type": "string"},
                "word_count": {"type": "integer"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "is_approved": {"enum": ["0"]},
                "rejection_reason": {"type": "string"}
            }
        },
        "questions": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["question_text","question_type","question_category","passage_id",
                             "question_image_url","part","option_a_text","option_b_text","option_c_text","option_d_text",
                             "is_correct","difficulty_level","explanation"],
                "properties": {
                    "question_text": {"type": "string"},
                    "question_type": {"type": "string", "enum": ["reading"]},
                    "question_category": {"type": "string", "enum": ["pos","tense","syntax","vocab"]},
                    "passage_id": {"type": ["string","null"]},
                    "question_image_url": {"type": ["string","null"]},
                    "part": {"type": "string", "enum": ["6"]},
                    "option_a_text": {"type": "string"},
                    "option_b_text": {"type": "string"},
                    "option_c_text": {"type": "string"},
                    "option_d_text": {"type": "string"},
                    "is_correct": {"enum": ["A","B","C","D"]},
                    "difficulty_level": {"enum": ["1","2","3","4","5"]},
                    "explanation": {"type": "string"}
                }
            }
        }
    }
}

# ===== Utils =====
class GenerateRequest(BaseModel):
    query_text: str = "Part 6 TOEIC grammar/vocab/syntax reading question"

def clean_text(text: str) -> str:
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

def generate_uuid() -> str:
    return str(uuid.uuid4())

@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "model": OPENAI_MODEL,
        "has_api_key": bool(OPENAI_API_KEY),
    }

# ===== 主路由 =====
@app.post("/generate_part6")
def generate_part6(req: GenerateRequest):
    try:
        # 1) 隨機情境
        scenario_keywords = ["企業發展","外食","娛樂","金融／預算","一般商務","保健",
                             "房屋／公司地產","製造業","辦公室","人事","採購","技術層面","旅遊"]
        scenario_text = random.choice(scenario_keywords)

        # 2) 查詢相似題 + 情境
        query_embedding = embedding_model.encode(req.query_text).tolist()
        res_q = collection.query(query_embeddings=[query_embedding], n_results=3)
        similar_questions = res_q["documents"][0] if res_q["documents"] else []
        sample_ctx = "\n".join(similar_questions[:2]) if similar_questions else "Example: (no similar found)"

        scenario_embedding = embedding_model.encode(scenario_text).tolist()
        res_s = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
        scenario_context = res_s["documents"][0][0] if res_s["documents"] else scenario_text

        # 3) 改寫後 Prompt
        prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列規則生成一題 TOEIC Part 6 文法/詞彙題組：

### 測驗情境：
{scenario_context}

### 範例題目（僅供風格參考）：
{sample_ctx}

### 題目生成規則：
1. 文章必須為 **商業英文文章**，主題與情境相關。
2. 文章中 **必須出現 4 個空格**（__1__ 到 __4__）。
3. 每個空格都要有 **四個選項 (A–D)**。
4. 每題 **必須有唯一正確答案**。
5. word_count 必須介於 60 到 80 字之間。為文章內容字數。
6. 只有 explanation 必須使用繁體中文並解釋選項文法或單字，其餘為英文。
7. 結果必須符合以下 Schema：
{json.dumps(TOEIC_PART6_SCHEMA, ensure_ascii=False, indent=2)}
"""

        # 4) 呼叫 OpenAI
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "toeic_part6",
                    "schema": TOEIC_PART6_SCHEMA,
                    "strict": True
                }
            }
        )

        raw_output = resp.choices[0].message.content
        cleaned_output = clean_text(raw_output or "")

        try:
            data = json.loads(cleaned_output)
            parsing_success = True
        except Exception as e:
            data = {"raw_output": cleaned_output, "error": str(e)}
            parsing_success = False

        # 5) 加上 UUID
        if parsing_success and "reading_passage" in data:
            passage_id = generate_uuid()
            data["reading_passage"]["passage_id"] = passage_id
            data["reading_passage"]["created_at"] = datetime.now().isoformat()
            data["reading_passage"]["updated_at"] = datetime.now().isoformat()

            for q in data.get("questions", []):
                q["question_id"] = generate_uuid()
                q["passage_id"] = passage_id
                q["created_at"] = datetime.now().isoformat()
                q["updated_at"] = datetime.now().isoformat()

            # 寫入 JSONL
            os.makedirs(os.path.dirname(JSONL_PATH), exist_ok=True)
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        return {"success": parsing_success, "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_part6:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
