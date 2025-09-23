
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from fastapi.concurrency import run_in_threadpool
# import chromadb
# from sentence_transformers import SentenceTransformer
# import httpx
# import random
# import json
# from datetime import datetime
# import demjson3 as demjson
# import re
# import uuid
# import os
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(title="TOEIC Part 2 Generator API")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"]
# )
# # -----------------------------
# # 配置
# # -----------------------------
# CHROMA_PATH = "/app/chroma_db"
# JSONL_PATH = "/app/json/toeic_part2_db_ready.jsonl"
# OLLAMA_API_URL = "http://ollama:11434/api/generate"

# embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
# chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# collection = chroma_client.get_collection("toeic_part2")
# scenario_collection = chroma_client.get_collection("toeic_scenarios")


# # -----------------------------
# # Pydantic 請求模型
# # -----------------------------
# class GenerateRequest(BaseModel):
#     query_text: str = "Part 2 TOEIC listening conversation with 3 option"

# # -----------------------------
# # 工具函數
# # -----------------------------
# def clean_text(text: str):
#     """移除非法字元"""
#     return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)




# def generate_uuid() -> str:
#     return str(uuid.uuid4())

# # -----------------------------
# # FastAPI 路由
# # -----------------------------
# @app.post("/generate_part2")
# def generate_part2(req: GenerateRequest):
#     # 選擇情境
#     scenario_keywords = [
#         "企業發展", "外食", "娛樂", "金融／預算", "一般商務", "保健", "房屋／公司地產",
#         "製造業", "辦公室", "人事", "採購", "技術層面", "旅遊"
#     ]
#     scenario_text = random.choice(scenario_keywords)

#     # # 查詢語意相似題目
#     # query_embedding = await run_in_threadpool(embedding_model.encode, req.query_text)
#     # results = collection.query(query_embeddings=[query_embedding], n_results=2)
#     # similar_questions = results["documents"][0] if results["documents"] else []

#     # scenario_embedding = await run_in_threadpool(embedding_model.encode, scenario_text)
#     # scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
#     # scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text
# # 查詢相似題目
#     query_embedding = embedding_model.encode(req.query_text).tolist()
#     results = collection.query(query_embeddings=[query_embedding], n_results=3)
#     similar_questions = results["documents"][0]

#     # 查詢情境範例
#     scenario_embedding = embedding_model.encode(scenario_text).tolist()
#     scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
#     scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

#     context = f"Example: {similar_questions[0][:500]}..."

#     # 🔧 prompt
#     prompt = f"""
# 你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，生成一題新的 TOEIC Part 2 聽力題組，包含：

# - 輸出json格式如下：
# {{
#   "toeic_listeningmaterial": {{
#     "audio_url": "",
#     "transcript": "Question. 這裡放問句內容，接三個選項",
#     "accent": "",
#     "topic": "{scenario_text}",
#     "speaker_count": "1",
#     "listening_level": "beginner,intermediate,advanced",
#   }},
#   "toeic_questions": [
#     {{
#       "question_text": "transcript問句內容,
#       "question_type": "listen",
#       "question_category": "（tense / pos / syntax / vocab 擇一",
#       "passage_id": null,
#       "question_image_url": null,
#       "part": "2",
#       "option_a_text": "選項 A",
#       "option_b_text": "選項 B",
#       "option_c_text": "選項 C",
#       "is_correct": "A",
#       "difficulty_level": "1-5",
#       "explanation": "解析",
#     }}
#   ]
# }}

# ### 測驗情境：
# {scenario_context}

# ### 範例題目：
# {context}
# 請特別注意：
# - 為題目一句問句，選項三句，選項必須出現在transcprit的題目後面，題目以對話或問答為主，含中文 explanation。
# - 商業英文自然專業、選項語意需接近且合文法。
# - explanation 須用繁體中文指出文法重點或語意差異，不可空泛。
# 請直接**輸出純 JSON，不要加入文字前綴或 Markdown**。
# """.strip()
#     # 5) 呼叫本地 LLM（Ollama）
    
#     # try:
#     #     async with httpx.AsyncClient(timeout=120.0) as client:
#     #         r = await client.post(
#     #             OLLAMA_API_URL,
#     #             json={"model": "llama3", "prompt": prompt, "stream": False}
#     #         )
#     #         r.raise_for_status()
#     #         raw_output = r.json().get("response", "")
#     # except httpx.HTTPError as e:
#     #     raise HTTPException(status_code=502, detail=f"Ollama 錯誤: {e}")
#     import requests
#     response = requests.post(
#         OLLAMA_API_URL,
#         json={
#             "model": "llama3",
#             "prompt": prompt,
#             "stream": False
#         }
#     )
#     raw_output = response.json()["response"]
#     cleaned_output = clean_text(raw_output)


#     # 嘗試解析 JSON
#     try:
#         data = json.loads(cleaned_output)
#     except json.JSONDecodeError:
#         data = demjson.decode(cleaned_output)

#     # 生成 UUID
#     material_id = generate_uuid()
#     data["toeic_listeningmaterial"]["material_id"] = material_id
#     for q in data["toeic_questions"]:
#         q["question_id"] = generate_uuid()
#         q["material_id"] = material_id

#     # 儲存 JSONL
#     with open(JSONL_PATH, "a", encoding="utf-8") as f:
#         f.write(json.dumps(data, ensure_ascii=False) + "\n")

#     return {"data": data}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("api_part2:app", host="0.0.0.0", port=11432, reload=True, log_level="debug")

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import random, json, re, uuid, os, traceback
from fastapi.middleware.cors import CORSMiddleware

# ===== App & CORS =====
app = FastAPI(title="TOEIC Part 2 Generator API (OpenAI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ===== Config =====
CHROMA_PATH = "/app/chroma_db"
JSONL_PATH  = "/app/json/toeic_part2_db_ready.jsonl"

OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")   # 可改成你要用的模型
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")                # 必填

# ===== OpenAI Client =====
from openai import OpenAI
client_kwargs = {}
client = OpenAI(api_key=OPENAI_API_KEY, **client_kwargs)     # 新版 SDK 用法（Responses API）  # :contentReference[oaicite:1]{index=1}

# ===== Embedding & Chroma =====
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client   = chromadb.PersistentClient(path=CHROMA_PATH)
collection           = chroma_client.get_collection("toeic_part2")
scenario_collection  = chroma_client.get_collection("toeic_scenarios")

# ===== Schema（強制模型輸出格式）=====
TOEIC_JSON_SCHEMA = {
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
                "speaker_count": {"type": "string"},
                "listening_level": {"enum": ["beginner","intermediate","advanced"]},
            }
        },
        "toeic_questions": {
            "type": "array",
            "minItems": 1, "maxItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["question_text","question_type","question_category","passage_id",
                             "question_image_url","part","option_a_text","option_b_text","option_c_text",
                             "is_correct","difficulty_level","explanation"],
                "properties": {
                    "question_text": {"type": "string"},
                    "question_type": {"type": "string", "enum": ["listen"]},
                    "question_category": {"type": "string", "enum": ["pos", "tense", "syntax", "vocab"]},
                    "passage_id": {"type": ["string","null"]},
                    "question_image_url": {"type": ["string","null"]},
                    "part": {"type": "string","enum": ["2"]},
                    "option_a_text": {"type": "string"},
                    "option_b_text": {"type": "string"},
                    "option_c_text": {"type": "string"},
                    "is_correct": {"enum": ["A","B","C"]},
                    "difficulty_level": {"enum":["1","2","3","4","5"]},
                    "explanation": {"type": "string"}
                }
            }
        }
    }
}

# ===== Utils =====
class GenerateRequest(BaseModel):
    query_text: str = "Part 2 TOEIC listening conversation with 3 option"

def clean_text(text: str) -> str:
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

def generate_uuid() -> str:
    return str(uuid.uuid4())

@app.get("/healthz")
def healthz():
    # 簡易健康檢查（不打 OpenAI，檢查必要設定）
    return {
        "ok": True,
        "model": OPENAI_MODEL,
        "has_api_key": bool(OPENAI_API_KEY),
    }

# ===== 核心路由 =====
@app.post("/generate_part2")
def generate_part2(req: GenerateRequest):
    try:
        # 1) 隨機挑情境
        scenario_keywords = ["企業發展","外食","娛樂","金融／預算","一般商務","保健",
                             "房屋／公司地產","製造業","辦公室","人事","採購","技術層面","旅遊"]
        scenario_text = random.choice(scenario_keywords)

        # 2) 檢索相似題 + 情境示例（保持你的設計）
        query_embedding = embedding_model.encode(req.query_text).tolist()
        res_q = collection.query(query_embeddings=[query_embedding], n_results=3)
        similar_questions = res_q["documents"][0] if res_q["documents"] else []
        sample_ctx = f"Example: {similar_questions[0][:500]}..." if similar_questions else "Example: (no similar found)"

        scenario_embedding = embedding_model.encode(scenario_text).tolist()
        res_s = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)
        scenario_context = res_s["documents"][0][0] if res_s["documents"] else scenario_text

        # 3) Prompt（交給 OpenAI Responses API，並用 JSON Schema 限制輸出）
        prompt = f"""
你是一位專業 TOEIC 出題專家。根據下列測驗情境與範例題目，生成一題新的 TOEIC Part 2 聽力題組（**只輸出 JSON，符合指定 Schema**）：

### 測驗情境：
{scenario_context}

### 範例題目：
{sample_ctx}

製作要點：
- 題目為一句問句；其後有三個選項（A/B/C），並在 transcript 中呈現。
- 商業英文需自然、專業；三個選項語意需接近且合文法。
- 只有explanation 用繁體中文，說明文法重點或語意差異，不可空泛。其他用英文。
- **嚴格遵守 JSON Schema**，不要有多餘欄位
- topic 請使用：{scenario_text}
"""

         #  新版 OpenAI SDK 呼叫
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "toeic_part2",
                    "schema": TOEIC_JSON_SCHEMA,
                    "strict": True
                }
            }
        )

        raw_output = getattr(resp, "choices", [])[0].message.content if hasattr(resp, "choices") else None
        cleaned_output = clean_text(raw_output or "")

        try:
            data = json.loads(cleaned_output)
            parsing_success = True
        except Exception:
            # Fallback: OpenAI 可能沒遵守 Schema → 返回原始結果
            data = {"raw_output": cleaned_output}
            parsing_success = False

       
# 6) 如果成功解析，補齊 UUID
        if parsing_success and "toeic_listeningmaterial" in data:
            material_id = generate_uuid()
            data["toeic_listeningmaterial"]["material_id"] = material_id
            for q in data.get("toeic_questions", []):
                q["question_id"] = generate_uuid()
                q["material_id"] = material_id

            # 追加寫入 JSONL（持久化）
            os.makedirs(os.path.dirname(JSONL_PATH), exist_ok=True)
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        # 7) 回傳給 n8n
        return {
            "success": parsing_success,
            "data": data
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI 回傳非 JSON，解析失敗：{e}")
    except Exception as e:
        # 回傳詳細堆疊，便於你現在排錯（上線可改為隱藏）
        raise HTTPException(status_code=500, detail=traceback.format_exc())

if __name__ == "__main__":
    import uvicorn
    # 建議固定 8000，讓 docker-compose 用 11432:8000 對映
    uvicorn.run("api_part2:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
