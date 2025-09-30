import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ⚙️ 設定你的 ChromaDB 儲存位置
CHROMA_PATH = "C:\\Users\\Fyn\\Desktop\\rag\\chroma_db"  # << 改成你的實際儲存路徑
COLLECTION_NAME = "toeic_questions"

# 🧠 載入嵌入模型
model = SentenceTransformer("all-MiniLM-L6-v2")

# 📄 載入題庫 CSV
df = pd.read_csv("part5.csv", encoding="big5")

# 🧠 啟動 ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


# 📌 取得目前資料庫內已儲存的 ID（一次最多支援1000筆查詢，視需求可分批查）
try:
    existing = collection.get(include=["ids"])
    existing_ids = set(existing["ids"])
except:
    existing_ids = set()

# 🚀 處理 CSV 資料
new_count = 0
for _, row in df.iterrows():
    if row['id'] in existing_ids:
        print(f"⚠️ 已存在：{row['id']}，略過")
        continue

    # 組合題目格式為純文字嵌入
    full_text = (
        f"{row['type']}\n"
        f"{row['question_text']}\n"
        f"(A) {row['option_a']}\n"
        f"(B) {row['option_b']}\n"
        f"(C) {row['option_c']}\n"
        f"(D) {row['option_d']}\n"
        f"Answer: {row['answer']}"
    )
    
    embedding = model.encode(full_text).tolist()
    
    collection.add(
        ids=[row['id']],
        documents=[full_text],
        embeddings=[embedding],
        metadatas=[{
            "type": row['type'],
        }]
    )

    print(f"✅ 已加入：{row['id']}")
    new_count += 1

print(f"\n✅ 完成：新增 {new_count} 筆題目至 ChromaDB")
