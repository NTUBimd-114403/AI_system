import subprocess
import os
from datetime import datetime

# 模型設定
MODEL_NAME = 'llama3:8b'
NUM_PARAGRAPHS = 2  # 每次產生幾組 Part 6 題組
OUTPUT_DIR = 'toeic_generated'  # 與 Part 5 / Part 7 共用
FILENAME_PREFIX = 'toeic_part6'

# Prompt：產生段落填空題
PROMPT_TEMPLATE = f"""
You are a TOEIC test writer. Please generate {NUM_PARAGRAPHS} TOEIC Part 6 (Text Completion) question sets.

Each set should include:
- A short passage (~80–120 words) with 4 numbered blanks (marked as (1), (2), (3), (4))
- 4 corresponding multiple-choice questions with 4 options each
- An answer key

Use only English. Use realistic business contexts (email, memo, notice, announcement, etc.)

Example Format:

【Passage Title】: (optional)

【Passage】:
Text with blanks labeled (1), (2), (3), (4)

【Questions and Options】:
Q1. (for blank 1)
A. option
B. option
C. option
D. option

...

【Answer Key】:
Q1: B  
Q2: A  
Q3: C  
Q4: D
"""

# 執行 ollama
def generate_part6():
    result = subprocess.run(
        ['ollama', 'run', MODEL_NAME],
        input=PROMPT_TEMPLATE,
        text=True,
        capture_output=True,
        encoding='utf-8' 
    )
    if result.returncode != 0:
        print("❌ Error calling Ollama:")
        print(result.stderr)
        return None
    return result.stdout.strip()

# 儲存題目
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
    print(f"📘 Generating {NUM_PARAGRAPHS} TOEIC Part 6 passages...")
    content = generate_part6()
    if content:
        save_to_file(content)
