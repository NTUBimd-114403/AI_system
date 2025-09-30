import openai
from django.core.management.base import BaseCommand
from toeic.models import Exam, ReadingPassage, Question, ExamQuestion, DIFFICULTY_LEVEL_CHOICES
import json
import uuid
import os
# 將金鑰寫死在程式碼中 (注意：實際應用應使用環境變數)
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")   # 可改成你要用的模型
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")  


class Command(BaseCommand):
    help = 'Generates a new TOEIC Part 7 Exam using OpenAI API.'

    def handle(self, *args, **options):
        self.stdout.write("正在請求 OpenAI 生成多益 Part 7 考題...")
        
        # 1. 向 OpenAI 請求生成文章與題目
        prompt = self.get_prompt()
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo", # 你也可以使用 gpt-4 或其他模型
                messages=[
                    {"role": "system", "content": "You are a professional TOEIC test content creator."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            data = json.loads(content)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"OpenAI API 請求失敗: {e}"))
            return

        # 2. 將生成結果存入資料庫
        self.stdout.write("OpenAI 生成完成，正在寫入資料庫...")
        try:
            # 創建 ReadingPassage
            passage_data = data['passage']
            passage = ReadingPassage.objects.create(
                title=passage_data['title'],
                content=passage_data['content'],
                translation=passage_data.get('translation', ''),
                word_count=len(passage_data['content'].split()),
                reading_level=passage_data['reading_level'],
                topic=passage_data['topic'],
                is_approved=0, # 預設為未審核
            )

            # 創建 Exam
            exam_title = f"Part 7 閱讀測驗 - {passage_data['title']}"
            exam = Exam.objects.create(
                title=exam_title,
                description=f"此為針對文章 '{passage_data['title']}' 生成的 Part 7 閱讀測驗。",
                exam_type='reading',
                part=7,
                duration_minutes=10, # 假設每篇文章10分鐘
                total_questions=len(data['questions']),
                passing_score=60.0,
            )

            # 創建 Question 和 ExamQuestion
            for i, q_data in enumerate(data['questions']):
                question = Question.objects.create(
                    question_type='reading',
                    passage=passage,
                    part=7,
                    question_text=q_data['question_text'],
                    option_a_text=q_data['options']['A'],
                    option_b_text=q_data['options']['B'],
                    option_c_text=q_data['options']['C'],
                    option_d_text=q_data['options']['D'],
                    is_correct=q_data['is_correct'],
                    difficulty_level=self.get_difficulty_level(q_data['difficulty_level']),
                    explanation=q_data['explanation'],
                    question_category=q_data.get('question_category', 'vocab'),
                )
                
                ExamQuestion.objects.create(
                    exam=exam,
                    question=question,
                    question_order=i + 1,
                    scores=100 / len(data['questions']), # 平均分配分數
                )

            self.stdout.write(self.style.SUCCESS(f"成功生成測驗：'{exam.title}'"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"資料庫寫入失敗: {e}"))

    def get_prompt(self):
        # 這是給 OpenAI 的指令，要求它生成指定格式的 JSON
        return """
        請扮演一個專業的多益測驗內容創作者，為我生成一篇 TOEIC Part 7 單篇文章的閱讀測驗。
        
        請嚴格遵循以下 JSON 格式輸出內容：
        {
          "passage": {
            "title": "文章標題",
            "content": "文章內容",
            "translation": "文章中文翻譯",
            "reading_level": "beginner|intermediate|advanced",
            "topic": "文章主題"
          },
          "questions": [
            {
              "question_text": "題目內容",
              "options": {
                "A": "選項 A",
                "B": "選項 B",
                "C": "選項 C",
                "D": "選項 D"
              },
              "is_correct": "A|B|C|D",
              "difficulty_level": "1|2|3|4|5",
              "explanation": "繁體中文答案解析",
              "question_category": "vocab|syntax|pos|tense",
              "question_num": "1"  # 題號
            },
            ... (至少3個題目)
          ]
        }
        
        文章內容需為商業書信、公告、新聞或廣告、行程表、客服回覆、會議記錄）等。
        文章內容字數必須在150~300字之間。
        可單篇至雙篇文章。
        難度等級請設定在 1 到 5 之間。
        題目數量為 3 到 5 題。
        """

    def get_difficulty_level(self, level_str):
        # 轉換 OpenAI 的難度等級字串為資料庫的整數
        try:
            return int(level_str)
        except (ValueError, IndexError):
            return 3 # 預設值