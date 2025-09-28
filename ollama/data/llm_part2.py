import chromadb
from sentence_transformers import SentenceTransformer
import requests
import random
import json
from datetime import datetime
import demjson3 as demjson
import re
import os

# 資料儲存設定
CHROMA_PATH = r"C:/Users/Fyn/Desktop/rag/chroma_db"
JSONL_PATH = "C:/Users/Fyn/Desktop/rag/json/toeic_part2_db_ready.jsonl"

# 初始化
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_collection("toeic_part2")
scenario_collection = chroma_client.get_collection("toeic_scenarios")

# 隨機選一個情境關鍵詞
scenario_keywords = [
    "企業發展", "外食", "娛樂", "金融／預算", "一般商務", "保健", "房屋／公司地產",
    "製造業", "辦公室", "人事", "採購", "技術層面", "旅遊"
]
scenario_text = random.choice(scenario_keywords)

# 查詢語意相關的範例題組與情境文字
query_embedding = embedding_model.encode("Part 2 TOEIC listening conversation with 3 option").tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=2)

scenario_embedding = embedding_model.encode(scenario_text).tolist()
scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)

similar_questions = results["documents"][0] if results["documents"] else []
scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

context = "\n\n".join(similar_questions)

# 🔧 產生 prompt（符合資料表格式）
prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，生成一題新的 TOEIC Part 2 聽力題組，包含：

1. 一筆 listening_material（不含 ID）
2. 一筆 question（不含 ID 與 material_id）
內容必須全為英文。
為題目一句問句，選項三句，選項必須出現在transcprit的題目後面，題目以對話或問答為主。
輸出 JSON 格式如下（不要有說明、標題、Markdown）:
{{
  "listening_material": {{
    "audio_url": "音檔 先留空",
    "transcript": "開頭一定要有 Question.後接題目內容(一句問句)，然後接選項內容(三句對應三個選項A,B,C)",
    "accent": "口音 先留空",
    "topic": "{scenario_text}",
    "speaker_count": "1",
    "listening_level": "難度(beginner,intermediate,advanced)",
    "created_at": "{datetime.now().isoformat()}",
    "updated_at": "{datetime.now().isoformat()}",
    "is_approved": "0",
    "rejection_reason": "先留空"
  }},
  "questions": [
    {{
      "question_text": "transcript 的題目一句",
      "question_type": "listen",
      "question_category": "題目種類(tense,pos,syntax,vocab)tense時態, pos詞性, syntax語法, vocab詞彙",
      "passage_id": null,
      "question_image_url": null,
      "part"= "2",
      "option_a_text": "transcrpit題目後的選項 A",
      "option_b_text": "transcrpit題目後的選項 B",
      "option_c_text": "transcrpit題目後的選項 C",
      "option_d_text": null,
      "is_correct": "正確回答(A, B, C)",
      "difficulty_level": "難度(1,2,3,4,5)數字越大越難",
      "explanation": "題目解析",
      "created_at": "{datetime.now().isoformat()}",
      "updated_at": "{datetime.now().isoformat()}"
    }}
  ]
}}

### 測驗情境：
{scenario_context}

### 範例題目（供風格參考）：
{context}

請確保輸出為合法的 JSON 陣列格式：
- 所有字串必須用雙引號包住
- 不可省略逗號
- `\n` 必須轉為字串表示（\\n），不可出現真正的換行
請直接輸出純 JSON 陣列，**不要有任何說明文字、標題、註解或 Markdown 格式。**
"""

# 🔄 發送請求至本地 LLM
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
)

raw_output = response.json()["response"]

# 處理非法字元
def clean_text(text):
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

cleaned_output = clean_text(raw_output)

try:
    data = json.loads(cleaned_output)
except json.JSONDecodeError:
    print("⚠️ JSON 解析錯誤，使用 demjson 嘗試解析...")
    data = demjson.decode(cleaned_output)

# 🚀 自動產生主鍵
import uuid

# 🔑 使用 UUID 產生 material_id 與 question_id
def generate_uuid():
    return str(uuid.uuid4())

material_id = generate_uuid()
data["listening_material"]["material_id"] = material_id

for q in data["questions"]:
    q["question_id"] = generate_uuid()
    q["material_id"] = material_id

# ✅ 儲存為 JSONL
with open(JSONL_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(data, ensure_ascii=False) + "\n")

print(f"✅ 題目已儲存至 {JSONL_PATH}")
print(f"🎯 本次主題：「{scenario_text}」")
print(f"📝 對話稿：\n{data['listening_material']['transcript'].replace('\\n', '\\n')}")
for q in data["questions"]:
    print("問題：", q["question_text"])
    print("A:", q["option_a_text"])
    print("B:", q["option_b_text"])
    print("C:", q["option_c_text"])
    print("D:", q["option_d_text"])
    print("ans:", q["is_correct"])
    print("explanation:", q["explanation"])
    print()
