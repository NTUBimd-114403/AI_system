# -*- coding: utf-8 -*-
# Assuming you have a file structure like this:
# project_root/
# ├── app_name/
# │   ├── models.py
# │   ├── ...
# └── import_phrases.py

# First, you need to set up the Django environment to be able to use models.
import os
import django

# Replace 'your_project_name' and 'app_name' with your actual project and app names.
# 例如: 'my_toeic_project.settings' 和 'toeic_app.models'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toeic_learn.settings')
django.setup()

from toeic.models import Phrase  # 這是已修正的行

def import_phrase_data():
    """
    從硬編碼的資料列表中匯入多益片語。
    """
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
        try:
            # 檢查片語是否已存在，避免重複匯入
            obj, created = Phrase.objects.get_or_create(
                title=phrase_data['title'],
                defaults={
                    'english_passage': phrase_data['english_passage'],
                    'chinese_translation': phrase_data['chinese_translation']
                }
            )
            if created:
                print(f"成功匯入片語: {obj.title}")
            else:
                print(f"片語已存在，跳過: {obj.title}")
        except Exception as e:
            print(f"匯入片語 {phrase_data['title']} 時發生錯誤: {e}")

if __name__ == "__main__":
    print("開始匯入片語資料...")
    import_phrase_data()
    print("片語資料匯入完成。")
