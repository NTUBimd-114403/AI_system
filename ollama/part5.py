import subprocess
import os
from datetime import datetime

# 設定模型與產生題數
MODEL_NAME = 'llama3:8b'
NUM_QUESTIONS = 5  # 每次生成幾題
OUTPUT_DIR = 'toeic_generated'
FILENAME_PREFIX = 'toeic_part5'

# Prompt 模板
PROMPT_TEMPLATE = f"""
You are a TOEIC test writer. Please generate {NUM_QUESTIONS} TOEIC Part 5 questions (Incomplete Sentences).
Each question should follow this format:

Q1. (incomplete sentence with one blank)
A. option A
B. option B
C. option C
D. option D

Answer: X

Example:
Q1. The manager ______ the proposal before the meeting.
A. review
B. reviews
C. reviewed
D. reviewing

Answer: C

Rules:
- Use only English
- Sentence topics should be TOEIC-appropriate (business, office, travel, HR, etc.)
- Vary grammar points (verb tense, preposition, articles, etc.)
- Keep it realistic and formal
- Do NOT explain the answers, just list them
"""

# 執行 Ollama 呼叫
def generate_questions():
    result = subprocess.run(
        ['ollama', 'run', MODEL_NAME],
        input=PROMPT_TEMPLATE,
        text=True,
        capture_output=True,
        encoding='utf-8'  
    )

    if result.returncode != 0:
        print("❌ Error running Ollama:")
        print(result.stderr)
        return None

    return result.stdout.strip()

# 儲存成 .txt 檔
def save_to_file(content):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{FILENAME_PREFIX}_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Saved to: {filepath}")

# 主程式
if __name__ == "__main__":
    print(f"📘 Generating {NUM_QUESTIONS} TOEIC Part 5 questions...")
    content = generate_questions()
    if content:
        save_to_file(content)
