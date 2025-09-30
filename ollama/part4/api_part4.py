from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb, random, json, re, uuid, os, traceback
from sentence_transformers import SentenceTransformer
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# ===== App =====
app = FastAPI(title="TOEIC Part 4 Generator API (OpenAI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ===== Config =====
CHROMA_PATH = "/app/chroma_db"
JSONL_PATH  = "/app/json/toeic_part4_db_ready.jsonl"
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client   = chromadb.PersistentClient(path=CHROMA_PATH)
collection      = chroma_client.get_collection("toeic_part4")
scenario_collection = chroma_client.get_collection("toeic_scenarios")

# ===== Schema =====
TOEIC_PART4_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["listening_material", "questions"],
    "properties": {
        "listening_material": {
            "type": "object",
            "additionalProperties": False,
            "required": ["audio_url","transcript","accent","topic","speaker_count","listening_level","is_approved","rejection_reason"],
            "properties": {
                "audio_url": {"type": "string"},
                "transcript": {"type": "string"},
                "accent": {"type": "string"},
                "topic": {"type": "string"},
                "speaker_count": {"type": "string"},
                "listening_level": {"enum": ["beginner","intermediate","advanced"]},
                "is_approved": {"type":"string"},
                "rejection_reason": {"type":"string"}
            }
        },
        "questions": {
            "type": "array",
            "additionalProperties": False,
            "minItems": 3, "maxItems": 3,
            "items": {
                "type":"object",
                "additionalProperties": False,
                "required": ["question_text","question_type","question_category","part",
                             "option_a_text","option_b_text","option_c_text","option_d_text",
                             "is_correct","difficulty_level","explanation"],
                "properties": {
                    "question_text": {"type":"string"},
                    "question_type": {"enum":["listen"]},
                    "question_category": {"enum":["pos","tense","syntax","vocab"]},
                    "part": {"enum":["3"]},
                    "option_a_text": {"type":"string"},
                    "option_b_text": {"type":"string"},
                    "option_c_text": {"type":"string"},
                    "option_d_text": {"type":"string"},
                    "is_correct": {"enum":["A","B","C","D"]},
                    "difficulty_level": {"enum":["1","2","3","4","5"]},
                    "explanation": {"type":"string"}
                }
            }
        }
    }
}

# ===== Utils =====
class GenerateRequest(BaseModel):
    scenario: str = None

def clean_text(text:str) -> str:
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

def generate_uuid() -> str:
    return str(uuid.uuid4())

# ===== Route =====
@app.post("/generate_part4")
def generate_part4(req: GenerateRequest):
    try:
        # 1) 情境
        scenario_keywords = ["企業發展","外食","娛樂","金融／預算","一般商務","保健",
                             "房屋／公司地產","製造業","辦公室","人事","採購","技術層面","旅遊"]
        scenario_text = req.scenario or random.choice(scenario_keywords)

        # 2) 相似題
        query_embedding = embedding_model.encode("TOEIC Part 4 listening monologue").tolist()
        res_q = collection.query(query_embeddings=[query_embedding], n_results=2)
        similar_questions = res_q["documents"][0] if res_q["documents"] else []
        sample_ctx = "\n".join(similar_questions)

        # 3) 情境
        scenario_embedding = embedding_model.encode(scenario_text).tolist()
        res_s = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
        scenario_context = res_s["documents"][0][0] if res_s["documents"] else scenario_text

        # 4) Prompt
        prompt = f"""
你是一位專業 TOEIC 出題專家。請生成一組新的 TOEIC Part 4 題組（1 段 talk + 3 題 question），並符合 Schema。
特別規範：
- listening_material.transcript 必須是 **單人獨白**（announcement / talk / telephone message）。
- 字數需 **控制在 80–120 words**（過短或過長都不符合 TOEIC 真題標準）。
- 開頭要包含 "Questions X through Y. Refer to the following ..."，接著才是正文。
- 商業英文自然專業，情境需真實，符合常見 TOEIC 場景（公司公告、答錄機留言、廣播通知、天氣預報、產品廣告等），請均勻分布。
- 三個問題必須能由 transcript 內容回答且須按照出現順序。
- question_category 請均勻涵蓋 pos/tense/syntax/vocab。
- explanation 請用繁體中文撰寫，且需具備教學意義（不只是翻譯）。
- 嚴格遵守 Schema，且 **只輸出 JSON**，不可以有多餘文字。
範例：{sample_ctx}
"""

        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role":"user","content":prompt}],
            response_format={
                "type":"json_schema",
                "json_schema":{"name":"toeic_part4","schema":TOEIC_PART4_SCHEMA,"strict":True}
            }
        )

        raw_output = resp.choices[0].message.content
        cleaned_output = clean_text(raw_output)
        data = json.loads(cleaned_output)

        # 5) 補 UUID
        material_id = generate_uuid()
        data["listening_material"]["material_id"] = material_id
        for q in data["questions"]:
            q["question_id"] = generate_uuid()
            q["material_id"] = material_id

        # 6) 寫入 JSONL
        os.makedirs(os.path.dirname(JSONL_PATH), exist_ok=True)
        with open(JSONL_PATH,"a",encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        return {"success":True,"data":data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

if __name__ == "__main__":
    import uvicorn
    # 建議固定 8000，讓 docker-compose 用 11432:8000 對映
    uvicorn.run("api_part4:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")