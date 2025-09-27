from django.core.management.base import BaseCommand
from toeic.models import Exam, ExamQuestion, ReadingPassage, Question
import math # 引入 math 模組用於 ceil 函數

class Command(BaseCommand):
    help = 'Generate Exam and ExamQuestions for all passages or parts, with Part 5 questions batched into 5 questions per exam.'

    def handle(self, *args, **options):
        self.stdout.write("開始建立 Exam 與 ExamQuestion ...")

        # 處理有文章的 part (例如 Part 6, 7) - 這部分保持不變
        passages = ReadingPassage.objects.all()
        for passage in passages:
            # 嘗試從 passage 或其第一個問題獲取 part 號碼
            part = getattr(passage, 'part', None)
            if part is None:
                first_question = passage.question_set.first()
                if first_question:
                    part = getattr(first_question, 'part', None)
            
            if part is None:
                self.stdout.write(f"跳過文章 {passage.title}，無法取得 part 號碼。")
                continue

            exam_title = f"Exam for Part {part} - {passage.title}"
            
            # 使用 get_or_create 避免重複建立 Exam
            exam, created = Exam.objects.get_or_create(
                title=exam_title,
                defaults={
                    'description': f"自動建立的測驗 (附文章，Part {part})",
                    'exam_type': 'toeic',
                    'part': part,
                    'duration_minutes': 20, # 預設文章類測驗時長
                    'total_questions': passage.question_set.count(),
                    'passing_score': 60,
                    'is_active': True,
                }
            )
            
            if not created:
                self.stdout.write(f"測驗 '{exam_title}' 已存在，跳過建立題目。")
                continue # 如果測驗已存在，則跳過為其添加題目，假設題目已存在

            questions = passage.question_set.all().order_by('created_at')
            for idx, question in enumerate(questions, start=1):
                ExamQuestion.objects.create(
                    exam=exam,
                    question=question,
                    question_order=idx,
                    scores=1.0,
                )
            self.stdout.write(f"成功建立測驗 '{exam_title}'，共 {questions.count()} 題。")

        # 處理無文章的 part，特別是 Part 5，每 5 題一個 Exam
        part_to_batch = 5 # 指定要分批處理的 Part 號碼
        
        # 獲取所有 Part 5 的題目，並按創建時間排序
        all_part_questions = list(Question.objects.filter(part=part_to_batch).order_by('created_at'))
        
        if not all_part_questions:
            self.stdout.write(f"Part {part_to_batch} 沒有題目，跳過分批建立測驗。")
        else:
            batch_size = 5 # 每組測驗的題目數量
            # 計算總共需要建立多少組測驗
            num_batches = math.ceil(len(all_part_questions) / batch_size) 

            self.stdout.write(f"Part {part_to_batch} 共有 {len(all_part_questions)} 題，將分為 {num_batches} 組。")

            for i in range(num_batches):
                start_index = i * batch_size
                end_index = start_index + batch_size
                # 獲取當前批次的題目
                current_batch_questions = all_part_questions[start_index:end_index]

                if not current_batch_questions:
                    continue # 避免空批次

                exam_set_number = i + 1 # 測驗組的編號
                exam_title = f"Exam for Part {part_to_batch} - Set {exam_set_number}"
                
                # 為每組題目建立一個新的 Exam
                exam, created = Exam.objects.get_or_create(
                    title=exam_title,
                    defaults={
                        'description': f"自動建立的測驗 (Part {part_to_batch} 第 {exam_set_number} 組，共 {len(current_batch_questions)} 題)",
                        'exam_type': 'toeic',
                        'part': part_to_batch,
                        'duration_minutes': 20, # 5 題建議時長，可根據實際情況調整
                        'total_questions': len(current_batch_questions),
                        'passing_score': 60, # 5 題建議及格分數
                        'is_active': True,
                    }
                )

                if not created:
                    self.stdout.write(f"測驗 '{exam_title}' 已存在，跳過建立題目。")
                    continue # 如果測驗已存在，則跳過為其添加題目，假設題目已存在

                # 將當前批次的題目加入到新建立的 Exam 中
                for idx, question in enumerate(current_batch_questions, start=1):
                    ExamQuestion.objects.create(
                        exam=exam,
                        question=question,
                        question_order=idx,
                        scores=1.0,
                    )
                self.stdout.write(f"成功建立測驗 '{exam_title}'，共 {len(current_batch_questions)} 題。")

        self.stdout.write("全部完成！")

