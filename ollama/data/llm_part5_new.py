import chromadb
from sentence_transformers import SentenceTransformer
import requests
import random
import json
from datetime import datetime
import re
import demjson3 as demjson

CHROMA_PATH = r"C:/Users/Fyn/Desktop/rag/chroma_db"
JSONL_PATH = "C:/Users/Fyn/Desktop/rag/json/toeic_part5_db_ready.jsonl"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_collection("toeic_questions")
scenario_collection = chroma_client.get_collection("toeic_scenarios")

# ➤ 隨機選擇一個情境關鍵詞
scenario_keywords = [
    "企業發展", "外食", "娛樂", "金融／預算", "一般商務", "保健", "房屋／公司地產",
    "製造業", "辦公室", "人事", "採購", "技術層面", "旅遊"
]
scenario_text = random.choice(scenario_keywords)

query_text = "Part 5 grammar/vocab/syntax TOEIC question"
query_embedding = embedding_model.encode(query_text).tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=3)

scenario_embedding = embedding_model.encode(scenario_text).tolist()
scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)

similar_questions = results["documents"][0]
scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

context = "\n\n".join(similar_questions)

prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，**生成一題新的 TOEIC Part 5 文法單句填空題**，並**以 JSON 陣列格式**回傳結果。每題包含：

請以 json 格式輸出如下（嚴格依照）：

{{
    "questions": {{
        "question_type": "reading",
        "question_category": "填入考點（tense / pos / syntax / vocab 擇一）",
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
        "explanation": "解析（請一定要寫出來，且有邏輯，不可空口無憑）",
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
- explanation 必須清楚指出語法重點或詞性邏輯，不可僅說「這是正確的」
請直接輸出純 JSON 陣列，**不要加入任何文字說明、標題或註解**，也**不要使用 markdown 格式標籤（```）**。

"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
)

# 取得回應文字並解析
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

# 🔑 使用 UUID 產生 question_id
def generate_uuid():
    return str(uuid.uuid4())
question_id = generate_uuid()
data["questions"]["question_id"] = question_id

# ✅ 儲存為 JSONL
with open(JSONL_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(data, ensure_ascii=False) + "\n")

    
print(f"✅ 題目已儲存至 {JSONL_PATH}")
print(f"🎯 本次主題：「{scenario_text}」")
print(f"題目 ID: {data['questions']['question_id']}")
print(f"題目: {data['questions']['question_text']}")
print(f"A: {data['questions']['option_a_text']}")
print(f"B: {data['questions']['option_b_text']}")
print(f"C: {data['questions']['option_c_text']}")
print(f"D: {data['questions']['option_d_text']}")
print(f"正確選項: {data['questions']['is_correct']}")
print(f"難度: {data['questions']['difficulty_level']}")
print(f"解析: {data['questions']['explanation']}")