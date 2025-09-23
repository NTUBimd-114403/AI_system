from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import random
from datetime import datetime
import re
import demjson3 as demjson
import json
import uuid
from fastapi.middleware.cors import CORSMiddleware
# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="TOEIC Part 5 Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
# -------------------------------
# ChromaDB & Embedding Setup
# -------------------------------
CHROMA_PATH = "/app/chroma_db"
JSONL_PATH = "/app/json/toeic_part5_db_ready.jsonl"
OLLAMA_API_URL = "http://host.docker.internal:11434/api/generate"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_collection("toeic_part5")
scenario_collection = chroma_client.get_collection("toeic_scenarios")

# -------------------------------
# Helper Functions
# -------------------------------
def clean_text(text: str):
    """移除非法字元"""
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

def generate_uuid():
    return str(uuid.uuid4())

# -------------------------------
# Request Model
# -------------------------------
class GenerateRequest(BaseModel):
    query_text: str = "Part 5 grammar/vocab/syntax TOEIC question"

# -------------------------------
# API Endpoint
# -------------------------------
@app.post("/generate_part5")
def generate_part5(req: GenerateRequest):
    # 隨機選擇一個情境
    scenario_keywords = [
        "企業發展", "外食", "娛樂", "金融／預算", "一般商務", "保健", "房屋／公司地產",
        "製造業", "辦公室", "人事", "採購", "技術層面", "旅遊"
    ]
    scenario_text = random.choice(scenario_keywords)

    # 查詢相似題目
    query_embedding = embedding_model.encode(req.query_text).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=3)
    similar_questions = results["documents"][0]

    # 查詢情境範例
    scenario_embedding = embedding_model.encode(scenario_text).tolist()
    scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
    scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

    context = "\n\n".join(similar_questions)

    # 組 prompt
    prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，**生成一題新的 TOEIC Part 5 文法單句填空題**，並**以 JSON 陣列格式**回傳結果。每題包含：

請以 json 格式輸出如下（嚴格依照）：

{{
    "questions": {{
        "question_type": "reading",
        "question_category": "考點（tense / pos / syntax / vocab 擇一）",
        "passage_id": null,
        "material_id": null,
        "question_text": "題目內容（含底線空格）",
        "part": 5,
        "option_a_text": "選項 A",
        "option_b_text": "選項 B",
        "option_c_text": "選項 C",
        "option_d_text": "選項 D",
        "is_correct": "正確選項（A, B, C 或 D）",
        "difficulty_level": "難度（1, 2, 3, 4, 5，數字越大越難）",
        "explanation": "正體中文解析，請明確指出語法/詞性/邏輯原因",
        "created_at": "{datetime.now().isoformat()}",
        "updated_at": "{datetime.now().isoformat()}"
    }}
}}

### 測驗情境：
{scenario_context}

### 範例題目（供風格參考）：
{context}

請特別注意：
- 題目須為商業英文常見句型，語句自然、用字專業
- 每個選項須與空格的語意及文法高度相關，不可太離題
- 題目不得出現明顯錯誤、模糊選項、文法不完整的情況
- explanation 必須用中文清楚指出語法重點或詞性邏輯與選項解釋，不可僅說「這是正確的」
請直接輸出純 JSON 陣列，**不要加入任何文字說明、標題或註解**，也**不要使用 markdown 格式標籤（```）**
"""

    # 這裡用 local LLM 生成題目
    import requests
    response = requests.post(
        OLLAMA_API_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    raw_output = response.json()["response"]
    cleaned_output = clean_text(raw_output)

    # 嘗試解析 JSON
    try:
        data = json.loads(cleaned_output)
    except json.JSONDecodeError:
        data = demjson.decode(cleaned_output)

    # 產生 UUID
    question_id = generate_uuid()
    data["questions"]["question_id"] = question_id

    # 儲存到 JSONL
    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

    return {
        "message": "TOEIC Part 5 題目生成成功",
        "scenario": scenario_text,
        "data": data
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_part5:app", host="0.0.0.0", port=11435, reload=True, log_level="debug")
