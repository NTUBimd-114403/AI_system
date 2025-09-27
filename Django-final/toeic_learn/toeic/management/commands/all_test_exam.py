# toeic/management/commands/create_all_test_exam.py

from django.core.management.base import BaseCommand
from toeic.models import Exam, ExamQuestion, Question
import random
import uuid
from django.utils import timezone  # 引入 timezone 模組

class Command(BaseCommand):
    help = 'Create a single comprehensive exam by selecting one random exam from each part.'

    def handle(self, *args, **options):
        self.stdout.write("開始建立 TOEIC 綜合測驗...")

        # 定義每個 Part 需要的 Exam Type
        PART_EXAM_TYPES = {
            2: 'listen',
            3: 'listen',
            5: 'reading',
            6: 'reading',
            7: 'reading',
        }
        
        all_questions = []
        total_questions_count = 0
        
        # 遍歷每個 Part，從現有的測驗中隨機選取一份
        for part_num, exam_type in PART_EXAM_TYPES.items():
            self.stdout.write(f"-> 正在為 Part {part_num} 尋找測驗...")
            
            # 找到所有符合條件的 Exam
            available_exams = Exam.objects.filter(part=part_num, exam_type=exam_type, is_active=True)
            
            if not available_exams.exists():
                self.stdout.write(self.style.WARNING(f"警告：找不到 Part {part_num} 的有效測驗。請在後台新增後再試。"))
                continue
            
            # 從找到的測驗中，隨機選取一份
            selected_exam = random.choice(available_exams)
            self.stdout.write(f"  - 已選取測驗: '{selected_exam.title}' (ID: {selected_exam.exam_id})")
            
            # 取得該測驗底下的所有題目，並添加到總題目列表中
            part_questions = list(ExamQuestion.objects.filter(exam=selected_exam).order_by('question_order'))
            
            # 確保有題目
            if not part_questions:
                self.stdout.write(self.style.WARNING(f"警告：選取的測驗 '{selected_exam.title}' 沒有任何題目。"))
                continue
            
            # 將 ExamQuestion 物件添加到總題目列表中
            all_questions.extend(part_questions)
            self.stdout.write(f"  - 已從該測驗中收集 {len(part_questions)} 題。")
        
        total_questions_count = len(all_questions)

        if total_questions_count == 0:
            self.stdout.write(self.style.ERROR("錯誤：未收集到任何題目，無法建立綜合測驗。請檢查後台資料。"))
            return

        # ------------------------------------------------------------------
        # 建立新的綜合測驗
        # ------------------------------------------------------------------
        # 使用時間戳記建立動態標題
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        exam_title = f"TOEIC 綜合測驗 - {timestamp}"
        
        exam = Exam.objects.create(
            title=exam_title,
            description=f"由 Part 2, 3, 5, 6, 7 隨機組合而成的綜合測驗 (建立於 {timestamp})",
            exam_type='mixed', # 使用 'mixed' 或其他標識符
            part=0,
            duration_minutes=60,
            total_questions=total_questions_count,
            passing_score=60,
            is_active=True,
        )
        
        self.stdout.write(self.style.SUCCESS(f"✅ 成功建立 Exam: {exam.title}"))

        # ------------------------------------------------------------------
        # 將題目與新的綜合測驗關聯起來
        # ------------------------------------------------------------------
        self.stdout.write("-> 正在將題目關聯到新的綜合測驗...")
        
        # 題目順序重新編號
        question_order = 1
        for eq in all_questions:
            ExamQuestion.objects.create(
                exam=exam,
                question=eq.question,  # 這裡使用 ExamQuestion 的 question 屬性
                question_order=question_order,
                scores=1.0,
            )
            question_order += 1
            
        self.stdout.write(self.style.SUCCESS(f"✅ 成功將 {total_questions_count} 題關聯到 {exam.title}。"))
        self.stdout.write("🎉 綜合測驗建立完成！")