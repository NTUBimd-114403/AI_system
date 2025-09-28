import json
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

CHROMA_PATH = "C:/Users/Fyn/Desktop/rag/chroma_db"
COLLECTION_NAME = "toeic_part2"

# 載入嵌入模型
model = SentenceTransformer("all-MiniLM-L6-v2")

# 啟動 ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# 取得目前已存在的 ID（最多1000筆，可依需求做分批擴充）
try:
    existing = collection.get(include=["ids"])
    existing_ids = set(existing["ids"])
except:
    existing_ids = set()

# 載入 Part 2 JSON 題組
with open("C:/Users/Fyn/Desktop/rag/part2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

new_count = 0
for item in data:
    id = item["id"]
    transcript = item["transcript"]

    if id in existing_ids:
        print(f"⚠️ 已存在：{id}，略過")
        continue

    # 組合嵌入文字
    options_text = "\n".join([f"{key}. {val}" for key, val in item.get("options", {}).items()])
    full_text = f"{item['transcript']}\n{options_text}"

    embedding = model.encode(full_text).tolist()

    # 加入到向量資料庫（注意 metadata 不要使用 dict/list 結構）
    collection.add(
        ids=[id],
        documents=[full_text],
        embeddings=[embedding],
        metadatas=[{
            "type": "part2",
            "num_questions": 1,
            "transcript_snippet": transcript[:100]
        }]
    )

    print(f"✅ 已加入：{id}")
    new_count += 1

print(f"\n🎉 完成：新增 {new_count} 筆 Part 2 題組至 ChromaDB")
