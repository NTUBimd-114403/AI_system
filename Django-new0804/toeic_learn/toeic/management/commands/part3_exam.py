# toeic/management/commands/generate_listening_exams_by_material.py
from django.core.management.base import BaseCommand
from toeic.models import Exam, ExamQuestion, ListeningMaterial

class Command(BaseCommand):
    help = 'Generate Exam and ExamQuestions for listening materials (Part 3, 4).'

    def handle(self, *args, **options):
        self.stdout.write("開始建立聽力 Exam（以 ListeningMaterial 為單位）...")

        # 過濾出 Part 3 和 Part 4 的聽力材料
        
         # 只取已審核通過的素材
        materials = ListeningMaterial.objects.filter(is_approved=True)
        for material in materials:
            first_question = material.question_set.first()
            if not first_question:
                self.stdout.write(f"跳過聽力 {material.topic}，無相關題目")
                continue
            
            # 只處理 Part 3 和 Part 4 的材料
            part = first_question.part
            if part not in [3, 4]:
                self.stdout.write(f"跳過非 Part 3/4 的材料：{material.topic} (Part {part})")
                continue

            # Exam title 加上 material_id，確保唯一性
            exam_title = f"Part 3 Listening Test - {material.topic} ({material.material_id})"
            
            # 使用 get_or_create 避免重複建立
            exam, created = Exam.objects.get_or_create(
                title=exam_title,
                defaults={
                    'description': "自動建立的聽力測驗",
                    'exam_type': 'listen',
                    'part': part,
                    'duration_minutes': 20,
                    'total_questions': material.question_set.count(),
                    'passing_score': 60,
                    'is_active': True,
                }
            )
            
            if not created:
                self.stdout.write(f"{exam_title} 已存在，跳過建立")
                continue

            # 建立 ExamQuestion
            questions = material.question_set.all().order_by('question_num')
            for idx, question in enumerate(questions, start=1):
                ExamQuestion.objects.create(
                    exam=exam,
                    question=question,
                    question_order=idx,
                    scores=1.0,
                )
            
            self.stdout.write(f"✅ 已建立：{exam_title}，共 {questions.count()} 題")

        self.stdout.write("🎉 所有 Part 3/4 的聽力 Exam 建立完成！")