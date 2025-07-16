import subprocess
import json
import os
from datetime import datetime

# ----- 設定區 -----
NUM_QUESTIONS = 3  # 想產生幾組 Part 7 題目
MODEL_NAME = 'llama3:8b'  # 或使用 llama3:70b（需更高記憶體）
OUTPUT_DIR = 'toeic_generated'
FILENAME_PREFIX = 'toeic_part7'
LANGUAGE = 'English'  # 或切換 'Chinese' 提示語言

# ----- Prompt 模板 -----
PROMPT_TEMPLATE = """
You are a professional TOEIC test writer. Please generate a TOEIC Reading Comprehension (Part 7) question set.

Follow this format strictly:

---
【Article Type】: (choose one: Email / Notice / Advertisement / News Article)
【Article Title】: (optional)
【Article Content】:
(Write an English passage with around 150–180 words. Topic should be business, travel, office, product announcement, etc.)

【Questions and Options】:
Q1. (question)
A. Option A
B. Option B
C. Option C
D. Option D

Q2. ...
Q3. ...

【Answer Key】:
Q1: A
Q2: C
Q3: D
---

Generate only one full set per response. Use only English.
"""

# ----- 主邏輯 -----
def generate_question():
    result = subprocess.run(
        ['ollama', 'run', MODEL_NAME],
        input=PROMPT_TEMPLATE,
        text=True,
        capture_output=True,
        encoding='utf-8'  # ✅ 加上這行
    )

    if result.returncode != 0:
        print("❌ Error running Ollama:")
        print(result.stderr)
        return None

    return result.stdout.strip()

def save_to_file(content, index):
    # 確保資料夾存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 產生時間戳檔名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{FILENAME_PREFIX}_{timestamp}_{index+1}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # 儲存成 txt
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Saved: {filepath}")

# ----- 執行區 -----
if __name__ == "__main__":
    for i in range(NUM_QUESTIONS):
        print(f"\n📘 Generating TOEIC Part 7 Question Set {i+1}/{NUM_QUESTIONS}...")
        content = generate_question()
        if content:
            save_to_file(content, i)


def generate_part7_data():
    result = subprocess.run(
        ['ollama', 'run', MODEL_NAME],
        input=PROMPT_TEMPLATE,
        text=True,
        capture_output=True,
        encoding='utf-8'
    )
    if result.returncode != 0:
        return None

    raw_text = result.stdout.strip()

    # 簡單解析標題與內容（可改進）
    title = ""
    content = ""

    for line in raw_text.splitlines():
        if "【Article Title】" in line:
            title = line.split("】:", 1)[-1].strip()
        if "【Article Content】" in line:
            content = ""
        elif "【Questions and Options】" in line:
            break
        else:
            content += line + "\n"

    return {"title": title or "Generated Passage", "content": content.strip()}
