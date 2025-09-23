import chromadb
from sentence_transformers import SentenceTransformer
import requests
import random
import json
from datetime import datetime
import re
import demjson3 as demjson
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
CHROMA_PATH = r"C:/Users/Fyn/Desktop/rag/chroma_db"
JSONL_PATH = "C:/Users/Fyn/Desktop/rag/data/toeic_part6_db_ready.jsonl"

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

query_text = "Part 6 grammar/vocab/syntax TOEIC question"
query_embedding = embedding_model.encode(query_text).tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=3)

scenario_embedding = embedding_model.encode(scenario_text).tolist()
scenario_results = scenario_collection.query(query_embeddings=[scenario_embedding], n_results=1)

similar_questions = results["documents"][0]
scenario_context = scenario_results["documents"][0][0] if scenario_results["documents"] else scenario_text

context = "\n\n".join(similar_questions)

prompt = f"""
你是一位專業 TOEIC 出題專家。請根據下列測驗情境與範例題目，**生成一題新的 TOEIC Part 6 文法單字填空題組包含四個空格**，並**以 JSON 陣列格式**回傳結果。
範例題目:
[
  {{
    "id": "part6_003",
    "title": "Notice for Carmel Tower Resident",
    "content": "On July 20, Carmel Tower will __1__ work on a refurbishment of the building's hallway. The project will take four weeks to complete. During this period, work crews will need to enter the building. __2__, access to the service elevator will be temporarily limited. Rest assured, efforts will be made to avoid __3__ to building occupants. However, some noise and dust may be anticipated. __4__. Contact the building management office if you have any concerns.",
    "questions": [
    {{
        "question": "1",
        "question_category":"vocab"
        "option": 
          "A": "interrupt",
          "B": "initiate",
          "C": "postpone",
          "D": "conclude",
        "answer": "B",
        "difficulty_level":"3",
        "explanation": "句意是「將會__大樓的走廊整修工程」，所有選項都是可能答案。因為只看空格所在的句子無法判斷答案，所以需要參考前後或整篇文章的內容。下一句提到工程將花費4周完成，所以要表達的應該是即將開始進行工程，答案是(B)initiate(開始)。(A)interrupt表示「打斷」，(C)postpone表示「延期」，(D)conclude表示「完成」。"
      }},
      {{
        "question": "2",
        "question_category":"vocab"
        "option": 
          "A": "Conversely",
          "B": "Formerly",
          "C": "Consequently",
          "D": "Similarly",
        "answer": "C",
        "difficulty_level":"3",
        "explanation": "空格和逗號一起出現在句首的連接副詞位置，所以要依照空格所在的句子和上一句的意義關係來選擇答案。上一句提到施工人員需要進入大樓，而空格所在的句子提到服務電梯的使用將暫時受限，所以表示前述內容造成結果的連接副詞結果，因此)是正確答案。(A)Conversely表示「相反地」，(B)Formerly表示「之前」，(D)Similarly表示「類似地」，使用在空格中都不洽當。"
      }},
      {{
        "question": "3",
        "question_category":"pos"
        "option": 
          "A": "disrupts",
          "B": "disrupted",
          "C": "disruptions",
          "D": "disrupt",
        "answer": "C",
        "difficulty_level":"3",
        "explanation": "只有名詞可以使用在及物動詞(avoid)的受詞位置，所以答案是名詞disruption(中斷，擾亂)的複數形(C)disruptions。動詞(A)動詞或過去分詞(B)動詞或形容詞(D)不能用在名詞的位置。"
      }},
      {{
        "question": "4",
        "option": 
          "A": "Severe weather has been forecast for this weekend.",
          "B": "Notices will be sent when the entrance has been reopened.",
          "C": "Every worker is responsible for keeping their area safe.",
          "D": "Please keep doors closed to minimize the inconvenience.",
        "answer": "D",
        "difficulty_level":"3",
        "explanation": "這是選擇適當句子的題目，所以需要參考前後或整篇文章的內容。前面提到Carmel Tower將開始進行大樓的走廊整修工程，而空格的上一句However, some noise and dust may be anticipated.提到預期將有若干噪音與粉塵，所以空格的內容應該和對居民造成不便有關，(D)Please keep doors closed to minimize the inconvenience是正確答案。"
      }}
    ]
  }}

請以 json 格式輸出如下（嚴格依照）：

{{
    "reading_passage": {{
    "topic": "{scenario_text}",
    "title": "標題",
    "reading_level": "難度(beginner,intermediate,advanced)",
    "content":"題目內容，包含四個空格"
    "created_at": "{datetime.now().isoformat()}",
    "updated_at": "{datetime.now().isoformat()}",
    "is_approved": "0",
    "rejection_reason": "先留空"
  }},
  "questions": [
    {{
      "question_text": "__1__",
      "question_type": "reading",
      "question_category": "題目種類(tense,pos,syntax,vocab)tense時態, pos詞性, syntax語法, vocab詞彙",
      "passage_id": null,
      "question_image_url": null,
      "part": "6",
      "option_a_text": "選項 A",
      "option_b_text": "選項 B",
      "option_c_text": "選項 C",
      "option_d_text": "選項 D",
      "is_correct": "正確解答(A, B, C, D)",
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

請特別注意：
- 題目須為商業英文常見句型，語句自然、用字專業
- 每個選項須與空格的語意及文法高度相關，不可太離題
- 題目不得出現明顯錯誤、模糊選項、文法不完整的情況
- explanation 必須用中文清楚指出語法重點或詞性邏輯與選項解釋，不可僅說「這是正確的」
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

passage_id = generate_uuid()
data["reading_passage"]["passage_id"] = passage_id

for q in data["questions"]:
    q["question_id"] = generate_uuid()
    q["passage_id"] = passage_id

# ✅ 儲存為 JSONL
with open(JSONL_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(data, ensure_ascii=False) + "\n")

    
print(f"✅ 題目已儲存至 {JSONL_PATH}")
print(f"🎯 本次主題：「{scenario_text}」")
for i, q in enumerate(data["questions"], 1):
    print(f"題目 {i} ID: {q['question_id']}")
    print(f"題目: {q['question_text']}")
    print(f"A: {q['option_a_text']}")
    print(f"B: {q['option_b_text']}")
    print(f"C: {q['option_c_text']}")
    print(f"D: {q['option_d_text']}")
    print(f"正確選項: {q['is_correct']}")
    print(f"難度: {q['difficulty_level']}")
    print(f"解析: {q['explanation']}")
    print("---------------")
