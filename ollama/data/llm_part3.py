import chromadb
from sentence_transformers import SentenceTransformer
import requests
import random
import json
from datetime import datetime
import demjson3 as demjson
import re
CHROMA_PATH = r"C:/Users/Fyn/Desktop/rag/chroma_db"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = chroma_client.get_collection("toeic_part3")  # 假設有專門 Part3 collection
scenario_collection = chroma_client.get_collection("toeic_scenarios")

# 隨機選擇一個情境關鍵詞
scenario_keywords = [
    "企業發展", "外食", "娛樂", "金融／預算", "一般商務", "保健", "房屋／公司地產",
    "製造業", "辦公室", "人事", "採購", "技術層面", "旅遊"
]
scenario_text = random.choice(scenario_keywords)

# 查詢示範題目，這裡用 Part 3 關鍵字
query_text = "Part 3 TOEIC listening conversation with 3 questions"
query_embedding = embedding_model.encode(query_text).tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=2)

scenario_embedding = embedding_model.encode(scenario_text).tolist()
scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)

similar_questions = results["documents"][0] if results["documents"] else []
scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

context = "\n\n".join(similar_questions)

prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，**生成一組新的 TOEIC Part 3 聽力對話題組**，包含對話稿與三個相關問題，每題包含問題內容、四個選項(A~D)、正確答案。

請以 JSON 陣列格式輸出，格式如下（嚴格遵守）：
[
  {{
    "transcript": "對話稿完整文字",
    "questions": [
      {{
        "question": "問題 1 內容",
        "option": {{
          "A": "選項 A",
          "B": "選項 B",
          "C": "選項 C",
          "D": "選項 D"
        }},
        "answer": "A"
      }},
      {{
        "question": "問題 2 內容",
        "option": {{
          "A": "選項 A",
          "B": "選項 B",
          "C": "選項 C",
          "D": "選項 D"
        }},
        "answer": "B"
      }},
      {{
        "question": "問題 3 內容",
        "option": {{
          "A": "選項 A",
          "B": "選項 B",
          "C": "選項 C",
          "D": "選項 D"
        }},
        "answer": "C"
      }}
    ]
  }}
]

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

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
)

raw_output = response.json()["response"]

def clean_text(text):
    return re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)

cleaned_output = clean_text(raw_output)

try:
    questions = json.loads(cleaned_output)
except json.JSONDecodeError as e:
    print("❌ JSON 格式錯誤，嘗試用 demjson 解析中...")
    try:
        questions = demjson.decode(cleaned_output)
    except Exception as e2:
        print("❌ demjson 解析失敗：", e2)
        print("🔎 原始回傳內容：", raw_output)
        raise e

# 輸出檔案路徑
output_path = "C:/Users/Fyn/Desktop/rag/json/toeic_part3.jsonl"

# 將結果加上時間與情境封裝
output_json = {
    "datetime": datetime.now().isoformat(),
    "scenario": scenario_text,
    "questions": questions
}

# 寫入 JSONL，避免重複寫入可以加檢查(此示範不包含重複判斷)
with open(output_path, "a", encoding="utf-8") as f:
    f.write(json.dumps(output_json, ensure_ascii=False) + "\n")

print(f"✅ 已將題目追加儲存至 {output_path}")
print(f"🎯 本次隨機情境：「{scenario_text}」\n")
print("✅ 生成的新題目：\n")
print(json.dumps(questions[0], ensure_ascii=False, indent=2))
