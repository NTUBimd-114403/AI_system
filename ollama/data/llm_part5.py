import chromadb
from sentence_transformers import SentenceTransformer
import requests
import random
import json
from datetime import datetime

CHROMA_PATH = r"C:/Users/Fyn/Desktop/rag/chroma_db"

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

query_text = "Part 5 grammar TOEIC question"
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
[
  {{
    "question": "題目內容（單句填空）",
    "option": {{
      "A": "選項 A",
      "B": "選項 B",
      "C": "選項 C",
      "D": "選項 D"
    }},
    "answer": "A",
    "explanation": "解析(請一定要寫出來，並且要有邏輯性)"
  }}
]
### 測驗情境：
{scenario_context}

### 範例題目（供風格參考）：
{context}

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

try:
    questions = json.loads(raw_output)

    # ➤ 強制轉成 list 統一格式
    if isinstance(questions, dict):
        questions = [questions]
    elif not isinstance(questions, list):
        raise ValueError("❌ LLM 回傳格式錯誤，無法轉為 list。")

    # ➤ 封裝成一筆 JSON 資料，加上時間與情境
    output_json = {
        "datetime": datetime.now().isoformat(),
        "scenario": scenario_text,
        "questions": questions
    }


    # ➤ 指定輸出檔案路徑
    output_path = "C:/Users/Fyn/Desktop/rag/json/toeic_part5.jsonl"

    # ➤ 寫入 JSONL（逐行儲存）
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(output_json, ensure_ascii=False) + "\n")

    # 顯示結果
    print(f"✅ 已將題目追加儲存至 {output_path}")
    print(f"🎯 本次隨機情境：「{scenario_text}」\n")
    print("✅ 生成的新題目（第一題範例）：\n")
    print(json.dumps(questions[0], ensure_ascii=False, indent=2))

except json.JSONDecodeError as e:
    print("❌ JSON 格式錯誤，無法解析 LLM 輸出：", e)
    print("🔎 原始 LLM 回應內容：\n", raw_output)
