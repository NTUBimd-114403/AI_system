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
file_path = "C:/Users/Fyn/Desktop/rag/json/toeic_part2_db_ready.jsonl"

with open(file_path, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

for item in data:
    material = item["toeic_listeningmaterial"]
    questions = item["toeic_questions"]

    # 插入 listening_material
    cursor.execute("""
        INSERT INTO toeic_listeningmaterial (
            material_id, transcript, audio_url, accent, topic,
            listening_level, is_approved
        ) VALUES ( %s,%s, %s, %s, %s, %s, %s)
    """, (
        material["material_id"],material["transcript"], material["audio_url"], material["accent"],
        material["topic"], material["listening_level"], material["is_approved"]
    ))

    # 插入 questions
    for q in questions:
        cursor.execute("""
            INSERT INTO toeic_question (
                question_id, material_id, question_text, question_type, question_category,
                part, option_a_text, option_b_text, option_c_text,
                is_correct, difficulty_level, explanation
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            q["question_id"], q["material_id"], q["question_text"], q["question_type"],
            q["question_category"], q["part"], q["option_a_text"], q["option_b_text"],
            q["option_c_text"], q["is_correct"], q["difficulty_level"],
            q["explanation"]
        ))

conn.commit()
cursor.close()
conn.close()

