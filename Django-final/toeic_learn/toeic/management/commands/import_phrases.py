# toeic/management/commands/import_phrases.py
from django.core.management.base import BaseCommand
from toeic.models import Phrase


class Command(BaseCommand):
    help = "匯入多益片語到資料庫"

    def handle(self, *args, **options):
        phrases = [
            {
                "title": "put off",
                "english_passage": "The meeting has been put off until Friday due to the manager's illness.",
                "chinese_translation": "v. 推遲；延期。例句翻譯：經理生病了，會議已被推遲到週五。"
            },
            {
                "title": "in accordance with",
                "english_passage": "All employees must follow the company's guidelines in accordance with the safety regulations.",
                "chinese_translation": "phr. 依照；根據。例句翻譯：所有員工都必須根據安全規定來遵守公司的指導方針。"
            },
            {
                "title": "look into",
                "english_passage": "We need to look into the customer's complaint and find a solution immediately.",
                "chinese_translation": "phr. 調查；研究。例句翻譯：我們需要調查客戶的投訴並立即找到解決方案。"
            },
            {
                "title": "account for",
                "english_passage": "Online sales account for over 60% of our total revenue this quarter.",
                "chinese_translation": "phr. 佔(某比例)；解釋。例句翻譯：線上銷售佔了本季度總收入的60%以上。"
            },
            {
                "title": "take on",
                "english_passage": "I am willing to take on more responsibilities to help the team succeed.",
                "chinese_translation": "phr. 承擔；接受(工作或責任)。例句翻譯：我願意承擔更多責任，以幫助團隊取得成功。"
            }
        ]

        for phrase_data in phrases:
            obj, created = Phrase.objects.get_or_create(
                title=phrase_data['title'],
                defaults={
                    'english_passage': phrase_data['english_passage'],
                    'chinese_translation': phrase_data['chinese_translation']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ 成功匯入: {obj.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ 已存在，跳過: {obj.title}"))
