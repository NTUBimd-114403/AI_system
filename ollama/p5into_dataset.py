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
file_path = "C:/Users/Fyn/Desktop/rag/json/toeic_part5_db_ready.jsonl"


with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        q = item["questions"]  # ✅ 這就是一題 dict，不需要再 for 了

        cursor.execute("""
            INSERT INTO toeic_question (
                question_id, material_id, question_text, question_type, question_category,
                part, option_a_text, option_b_text, option_c_text, option_d_text,
                is_correct, difficulty_level, explanation, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            q["question_id"], q["material_id"], q["question_text"], q["question_type"],
            q["question_category"], q["part"], q["option_a_text"], q["option_b_text"],
            q["option_c_text"], q["option_d_text"], q["is_correct"], q["difficulty_level"],
            q["explanation"], q["created_at"], q["updated_at"]
        ))


conn.commit()
cursor.close()
conn.close()

