import json
import mysql.connector
from datetime import datetime

# 資料庫連線
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="114_system",
    charset='utf8mb4',
    collation='utf8mb4_general_ci'
)
cursor = conn.cursor()

# 載入 JSON 檔案（或你也可以直接貼入 JSON 字串）
file_path = "C:/Users/Fyn/Desktop/rag/json/toeic_part6_db_ready.jsonl"

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

for item in data:  # item 是 dict
    passage_id = item["passage_id"]
    reading = item["data"]["reading_passage"]
    questions = item["data"]["questions"]

    # 插入 reading
    cursor.execute("""
        INSERT INTO toeic_readingpassage (
            passage_id, title, content, word_count, topic,
            reading_level, created_at, updated_at, is_approved, rejection_reason
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        passage_id, reading["title"], reading["content"], reading.get("word_count", 0),
        reading["topic"], reading["reading_level"],
        reading["created_at"], reading["updated_at"], int(reading["is_approved"]), reading["rejection_reason"]
    ))

    # 插入 questions
    for q in questions:
        cursor.execute("""
            INSERT INTO toeic_question (
                question_id, material_id, question_text, question_type, question_category,
                part, option_a_text, option_b_text, option_c_text, option_d_text,
                is_correct, difficulty_level, explanation, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            q["question_id"], passage_id, q["question_text"], q["question_type"],
            q["question_category"], q["part"], q["option_a_text"], q["option_b_text"],
            q["option_c_text"], q["option_d_text"], q["is_correct"], q["difficulty_level"],
            q["explanation"], q["created_at"], q["updated_at"]
        ))

conn.commit()
cursor.close()
conn.close()

