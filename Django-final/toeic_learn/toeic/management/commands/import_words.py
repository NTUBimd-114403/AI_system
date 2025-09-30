from django.core.management.base import BaseCommand
from toeic.models import DailyVocabulary
from django.db.utils import IntegrityError
import re

class Command(BaseCommand):
    """
    一個Django管理命令，用於將商業與人力資源相關的單字匯入資料庫。
    """
    help = 'Imports business and HR-related vocabulary into the database.'

    def handle(self, *args, **options):
        # 商業與人力資源相關的單字列表
        words_to_import = [
            {
                "word": "stream",
                "part_of_speech": "n, v",
                "translation": "小河；溪流 (n)；流；流動 (v)",
                "pronunciation": "/striːm/",
                "example_sentence": "A small stream runs through the forest.",
                "example_translation": "一條小溪流經森林。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "streamline",
                "part_of_speech": "adj.",
                "translation": "流線型的",
                "pronunciation": "/ˈstriːmlaɪn/",
                "example_sentence": "We need to streamline our business processes to increase efficiency.",
                "example_translation": "我們需要簡化業務流程以提高效率。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "strength",
                "part_of_speech": "n",
                "translation": "力氣；實力；強度",
                "pronunciation": "/streŋθ/",
                "example_sentence": "He doesn't have the strength to lift the box.",
                "example_translation": "他沒有力氣舉起那個箱子。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "strengthen",
                "part_of_speech": "v",
                "translation": "增強；鞏固",
                "pronunciation": "/ˈstreŋθən/",
                "example_sentence": "The company plans to strengthen its presence in the market.",
                "example_translation": "公司計劃增強其在市場上的影響力。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "stress",
                "part_of_speech": "n, v",
                "translation": "壓力；緊張；著重 (n)；強調；著重 (v)",
                "pronunciation": "/stres/",
                "example_sentence": "He is under a lot of stress at work.",
                "example_translation": "他在工作上承受很大的壓力。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "stretch",
                "part_of_speech": "n, v",
                "translation": "伸直；展開；曲解 (n)；伸縮；延續；吹牛 (v)",
                "pronunciation": "/stretʃ/",
                "example_sentence": "It's important to stretch before you exercise.",
                "example_translation": "運動前熱身是很重要的。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "strike",
                "part_of_speech": "v, n",
                "translation": "打擊；攻擊 (v)；罷工；打擊 (n)",
                "pronunciation": "/straɪk/",
                "example_sentence": "The workers went on strike for better pay.",
                "example_translation": "工人們為了爭取更好的薪水而罷工。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "strive",
                "part_of_speech": "v",
                "translation": "力爭；苦幹",
                "pronunciation": "/straɪv/",
                "example_sentence": "We must strive to achieve our goals.",
                "example_translation": "我們必須努力達成我們的目標。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "structure",
                "part_of_speech": "n, v",
                "translation": "結構 (n)；構造 (v)",
                "pronunciation": "/ˈstrʌktʃər/",
                "example_sentence": "The building has a solid steel structure.",
                "example_translation": "這棟建築物有堅固的鋼結構。",
                "difficulty_level": 2,
                "related_category": "Academic"
            },
            {
                "word": "study",
                "part_of_speech": "n, v",
                "translation": "學習；研究 (n)；學習；研究 (v)",
                "pronunciation": "/ˈstʌdi/",
                "example_sentence": "She studies hard for her exams.",
                "example_translation": "她為考試而努力學習。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "style",
                "part_of_speech": "n",
                "translation": "風格；作風",
                "pronunciation": "/staɪl/",
                "example_sentence": "I like her style of writing.",
                "example_translation": "我喜歡她的寫作風格。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "subject",
                "part_of_speech": "n, v",
                "translation": "主題；題目 (n)；易受⋯；易患⋯ (v)",
                "pronunciation": "/ˈsʌbdʒɪkt/",
                "example_sentence": "The subject of the book is climate change.",
                "example_translation": "這本書的主題是氣候變遷。",
                "difficulty_level": 2,
                "related_category": "Academic"
            },
            {
                "word": "subjectively",
                "part_of_speech": "adv.",
                "translation": "主觀地",
                "pronunciation": "/səbˈdʒektɪvli/",
                "example_sentence": "It's difficult to evaluate art subjectively.",
                "example_translation": "要主觀地評估藝術是很困難的。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "submit",
                "part_of_speech": "v",
                "translation": "屈從；忍受；提交；呈遞；主張",
                "pronunciation": "/səbˈmɪt/",
                "example_sentence": "You must submit your report by Friday.",
                "example_translation": "你必須在星期五前提交你的報告。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "subordinate",
                "part_of_speech": "adj., n",
                "translation": "次要的；隸屬的 (adj.)；部下；部屬 (n)",
                "pronunciation": "/səˈbɔːrdɪnət/",
                "example_sentence": "He is a subordinate to the manager.",
                "example_translation": "他是經理的部下。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "subscribe",
                "part_of_speech": "v",
                "translation": "訂閱；同意",
                "pronunciation": "/səbˈskraɪb/",
                "example_sentence": "I subscribed to the online magazine.",
                "example_translation": "我訂閱了這本線上雜誌。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "subscription",
                "part_of_speech": "n",
                "translation": "訂閱；同意",
                "pronunciation": "/səbˈskrɪpʃən/",
                "example_sentence": "The subscription fee is 10 dollars per month.",
                "example_translation": "訂閱費用是每月10美元。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "subside",
                "part_of_speech": "v",
                "translation": "消退；平息；減弱",
                "pronunciation": "/səbˈsaɪd/",
                "example_sentence": "The flood waters finally began to subside.",
                "example_translation": "洪水終於開始消退。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "subsidiary",
                "part_of_speech": "adj.",
                "translation": "輔助的；附帶的",
                "pronunciation": "/səbˈsɪdiəri/",
                "example_sentence": "The company has a subsidiary in Japan.",
                "example_translation": "這家公司在日本有一家子公司。",
                "difficulty_level": 4,
                "related_category": "Business"
            },
            {
                "word": "subsidize",
                "part_of_speech": "v",
                "translation": "補助；資助",
                "pronunciation": "/ˈsʌbsɪdaɪz/",
                "example_sentence": "The government subsidizes public transportation.",
                "example_translation": "政府補助大眾運輸。",
                "difficulty_level": 4,
                "related_category": "Business"
            },
            {
                "word": "subsidy",
                "part_of_speech": "n",
                "translation": "津貼；補貼",
                "pronunciation": "/ˈsʌbsɪdi/",
                "example_sentence": "The company receives a government subsidy for its research.",
                "example_translation": "這家公司獲得了政府的研究津貼。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "substantial",
                "part_of_speech": "adj.",
                "translation": "真實的；堅固的",
                "pronunciation": "/səbˈstænʃəl/",
                "example_sentence": "He made a substantial contribution to the project.",
                "example_translation": "他對這個專案做出了實質性的貢獻。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "substantiate",
                "part_of_speech": "v",
                "translation": "證實；證明",
                "pronunciation": "/səbˈstænʃieɪt/",
                "example_sentence": "The lawyer couldn't substantiate the client's claims.",
                "example_translation": "律師無法證實客戶的主張。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "substitute",
                "part_of_speech": "n, v, adj.",
                "translation": "代替人；代替物 (n)；代替 (v)；代替的 (adj.)",
                "pronunciation": "/ˈsʌbstɪtuːt/",
                "example_sentence": "The coach used a substitute player in the second half.",
                "example_translation": "教練在下半場使用了一名替補球員。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "subtract",
                "part_of_speech": "v",
                "translation": "減去；去掉",
                "pronunciation": "/səbˈtrækt/",
                "example_sentence": "If you subtract 5 from 10, you get 5.",
                "example_translation": "如果你從10減去5，你會得到5。",
                "difficulty_level": 1,
                "related_category": "Academic"
            },
            {
                "word": "subway",
                "part_of_speech": "n",
                "translation": "地下鐵",
                "pronunciation": "/ˈsʌbweɪ/",
                "example_sentence": "I take the subway to work every day.",
                "example_translation": "我每天搭地鐵去上班。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "succeed",
                "part_of_speech": "v",
                "translation": "成功；繼任",
                "pronunciation": "/səkˈsiːd/",
                "example_sentence": "She succeeded in her goal of becoming a doctor.",
                "example_translation": "她成功實現了成為醫生的目標。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "success",
                "part_of_speech": "n",
                "translation": "成功；成就",
                "pronunciation": "/səkˈses/",
                "example_sentence": "Hard work is the key to success.",
                "example_translation": "努力工作是成功的關鍵。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "sufficient",
                "part_of_speech": "adj.",
                "translation": "足夠的；充分的",
                "pronunciation": "/səˈfɪʃənt/",
                "example_sentence": "There is sufficient food for everyone.",
                "example_translation": "有足夠的食物給每個人。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "suggest",
                "part_of_speech": "v",
                "translation": "建議",
                "pronunciation": "/səˈdʒest/",
                "example_sentence": "I suggest we take a break now.",
                "example_translation": "我建議我們現在休息一下。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "suggestion",
                "part_of_speech": "n",
                "translation": "建議",
                "pronunciation": "/səˈdʒestʃən/",
                "example_sentence": "I have a suggestion for the new project.",
                "example_translation": "我對新專案有一個建議。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "suit",
                "part_of_speech": "n, v",
                "translation": "西裝；套；副 (n)；相稱；彼此協調 (v)",
                "pronunciation": "/suːt/",
                "example_sentence": "This color really suits you.",
                "example_translation": "這個顏色真的很適合你。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "suitable",
                "part_of_speech": "adj.",
                "translation": "適當的；合適的",
                "pronunciation": "/ˈsuːtəbl/",
                "example_sentence": "This movie is not suitable for children.",
                "example_translation": "這部電影不適合兒童。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "suitcase",
                "part_of_speech": "n",
                "translation": "小型旅行箱；手提箱",
                "pronunciation": "/ˈsuːtkeɪs/",
                "example_sentence": "I packed my suitcase for the trip.",
                "example_translation": "我為旅行打包了我的手提箱。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "suite",
                "part_of_speech": "n",
                "translation": "套房；隨從",
                "pronunciation": "/swiːt/",
                "example_sentence": "We booked a luxury suite for our stay.",
                "example_translation": "我們為住宿訂了一間豪華套房。",
                "difficulty_level": 2,
                "related_category": "Travel"
            },
            {
                "word": "sum",
                "part_of_speech": "n, v",
                "translation": "總數；總和 (n)；總結 (v)",
                "pronunciation": "/sʌm/",
                "example_sentence": "The sum of 2 and 3 is 5.",
                "example_translation": "2和3的總和是5。",
                "difficulty_level": 2,
                "related_category": "Academic"
            },
            {
                "word": "summarize",
                "part_of_speech": "v",
                "translation": "作總結；作概括",
                "pronunciation": "/ˈsʌməraɪz/",
                "example_sentence": "Can you summarize the main points of the report?",
                "example_translation": "你能總結一下這份報告的要點嗎？",
                "difficulty_level": 2,
                "related_category": "Academic"
            },
            {
                "word": "superb",
                "part_of_speech": "adj.",
                "translation": "堂皇的；宏偉的",
                "pronunciation": "/suːˈpɜːrb/",
                "example_sentence": "The view from the top of the mountain was superb.",
                "example_translation": "從山頂看下去的景色非常壯麗。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "superior",
                "part_of_speech": "adj.",
                "translation": "較高的；上級的；高傲的",
                "pronunciation": "/suːˈpɪəriər/",
                "example_sentence": "This new model is superior to the old one.",
                "example_translation": "這個新模型比舊的好。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "supervise",
                "part_of_speech": "v",
                "translation": "監督；管理",
                "pronunciation": "/ˈsuːpərvaɪz/",
                "example_sentence": "He was hired to supervise the new team.",
                "example_translation": "他被聘請來監督新團隊。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "supervisor",
                "part_of_speech": "n",
                "translation": "管理人；指導者",
                "pronunciation": "/ˈsuːpərvaɪzər/",
                "example_sentence": "My supervisor gave me a positive performance review.",
                "example_translation": "我的主管給了我一個正面的績效評估。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "supervisory",
                "part_of_speech": "adj.",
                "translation": "管理（員）的",
                "pronunciation": "/ˌsuːpərˈvaɪzəri/",
                "example_sentence": "The new job has more supervisory responsibilities.",
                "example_translation": "這個新工作有更多的管理職責。",
                "difficulty_level": 4,
                "related_category": "Business"
            },
            {
                "word": "supplement",
                "part_of_speech": "n",
                "translation": "增補，補充；副刊",
                "pronunciation": "/ˈsʌpləmənt/",
                "example_sentence": "I take a daily vitamin supplement.",
                "example_translation": "我每天服用維生素補充劑。",
                "difficulty_level": 3,
                "related_category": "DailyLife"
            },
            {
                "word": "supplementary",
                "part_of_speech": "adj.",
                "translation": "增補的；補充的",
                "pronunciation": "/ˌsʌpləˈmentəri/",
                "example_sentence": "The teacher provided supplementary materials for the lesson.",
                "example_translation": "老師為課程提供了補充材料。",
                "difficulty_level": 3,
                "related_category": "Academic"
            },
            {
                "word": "supplier",
                "part_of_speech": "n",
                "translation": "供應者",
                "pronunciation": "/səˈplaɪər/",
                "example_sentence": "Our main supplier is located in China.",
                "example_translation": "我們的主要供應商位於中國。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "supply",
                "part_of_speech": "n, v",
                "translation": "供給；供應 (n)；供給；供應 (v)",
                "pronunciation": "/səˈplaɪ/",
                "example_sentence": "The demand for the product exceeds the supply.",
                "example_translation": "對該產品的需求超過了供應。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "support",
                "part_of_speech": "v, n",
                "translation": "支持；擁護 (v)；支持；擁護 (n)",
                "pronunciation": "/səˈpɔːrt/",
                "example_sentence": "We support her decision to quit her job.",
                "example_translation": "我們支持她辭職的決定。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "supportive",
                "part_of_speech": "adj.",
                "translation": "支援的；贊助的",
                "pronunciation": "/səˈpɔːrtɪv/",
                "example_sentence": "My family has always been very supportive of my career.",
                "example_translation": "我的家人一直非常支持我的事業。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "suppose",
                "part_of_speech": "v",
                "translation": "猜想；以為",
                "pronunciation": "/səˈpoʊz/",
                "example_sentence": "I suppose you're right.",
                "example_translation": "我想你是對的。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "surely",
                "part_of_speech": "adv.",
                "translation": "確實；無疑",
                "pronunciation": "/ˈʃʊərli/",
                "example_sentence": "Surely you don't believe that story?",
                "example_translation": "你確定你不相信那個故事嗎？",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "surface",
                "part_of_speech": "n, adj., v",
                "translation": "面；表面 (n)；表面的；外觀的 (adj.)；顯露；呈現 (v)",
                "pronunciation": "/ˈsɜːrfɪs/",
                "example_sentence": "The surface of the moon is covered in craters.",
                "example_translation": "月球表面覆蓋著隕石坑。",
                "difficulty_level": 2,
                "related_category": "Academic"
            },
            {
                "word": "surmise",
                "part_of_speech": "v, n",
                "translation": "推測；猜測 (v)；推測；猜測 (n)",
                "pronunciation": "/sərˈmaɪz/",
                "example_sentence": "He surmised that the suspect had fled the country.",
                "example_translation": "他推測嫌疑犯已經逃離了這個國家。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "surplus",
                "part_of_speech": "n, adj.",
                "translation": "剩餘物；順差 (n)；過剩的；剩餘的 (adj.)",
                "pronunciation": "/ˈsɜːrpləs/",
                "example_sentence": "We have a surplus of food and a shortage of water.",
                "example_translation": "我們食物過剩，但水資源短缺。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "surprise",
                "part_of_speech": "v, n",
                "translation": "驚喜；驚訝 (v)；驚喜；意外 (n)",
                "pronunciation": "/sərˈpraɪz/",
                "example_sentence": "The birthday party was a complete surprise.",
                "example_translation": "這個生日派對完全是個驚喜。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "survey",
                "part_of_speech": "n, v",
                "translation": "問卷 (n)；調查；做問卷 (v)",
                "pronunciation": "/ˈsɜːrveɪ/",
                "example_sentence": "The company conducted a survey to understand customer satisfaction.",
                "example_translation": "公司進行了一項調查，以了解客戶滿意度。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "survive",
                "part_of_speech": "v",
                "translation": "生存；生還",
                "pronunciation": "/sərˈvaɪv/",
                "example_sentence": "Few people survived the plane crash.",
                "example_translation": "很少有人在墜機事故中倖存。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "susceptible",
                "part_of_speech": "adj.",
                "translation": "易被感動的；敏感的",
                "pronunciation": "/səˈseptəbl/",
                "example_sentence": "He is susceptible to flattery.",
                "example_translation": "他很容易受到諂媚的影響。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "suspect",
                "part_of_speech": "v",
                "translation": "懷疑；不信任",
                "pronunciation": "/səˈspekt/",
                "example_sentence": "I suspect that he is hiding something.",
                "example_translation": "我懷疑他在隱藏什麼。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "suspend",
                "part_of_speech": "v",
                "translation": "懸掛；使飄浮",
                "pronunciation": "/səˈspend/",
                "example_sentence": "The light fixture was suspended from the ceiling.",
                "example_translation": "燈具懸掛在天花板上。",
                "difficulty_level": 3,
                "related_category": "Academic"
            },
            {
                "word": "sustain",
                "part_of_speech": "v",
                "translation": "支撐；承受",
                "pronunciation": "/səˈsteɪn/",
                "example_sentence": "The bridge is able to sustain heavy loads.",
                "example_translation": "這座橋能夠承受重物。",
                "difficulty_level": 3,
                "related_category": "Academic"
            },
            {
                "word": "sweater",
                "part_of_speech": "n",
                "translation": "毛線衣",
                "pronunciation": "/ˈswetər/",
                "example_sentence": "It's cold outside, so I'm wearing a sweater.",
                "example_translation": "外面很冷，所以我穿了一件毛衣。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "swift",
                "part_of_speech": "adj.",
                "translation": "快速的；快捷的",
                "pronunciation": "/swɪft/",
                "example_sentence": "He made a swift recovery from his illness.",
                "example_translation": "他從疾病中迅速康復。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "switch",
                "part_of_speech": "n, v",
                "translation": "開關；轉換 (n)；改變；轉移 (v)",
                "pronunciation": "/swɪtʃ/",
                "example_sentence": "Could you flip the light switch?",
                "example_translation": "你能把電燈開關打開嗎？",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "sympathetic",
                "part_of_speech": "adj.",
                "translation": "同情的",
                "pronunciation": "/ˌsɪmpəˈθetɪk/",
                "example_sentence": "He was very sympathetic when I told him about my problem.",
                "example_translation": "當我告訴他我的問題時，他非常同情。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "sympathize",
                "part_of_speech": "v",
                "translation": "同情；憐憫",
                "pronunciation": "/ˈsɪmpəθaɪz/",
                "example_sentence": "I sympathize with your situation.",
                "example_translation": "我同情你的處境。",
                "difficulty_level": 5,
                "related_category": "DailyLife"
            },
            {
                "word": "sympathy",
                "part_of_speech": "n",
                "translation": "同情；同情心",
                "pronunciation": "/ˈsɪmpəθi/",
                "example_sentence": "She expressed her sympathy for his loss.",
                "example_translation": "她對他的損失表達了同情。",
                "difficulty_level": 2,
                "related_category": "DailyLife"
            },
            {
                "word": "symposium",
                "part_of_speech": "n",
                "translation": "討論會；座談會",
                "pronunciation": "/sɪmˈpoʊziəm/",
                "example_sentence": "He gave a presentation at the international symposium.",
                "example_translation": "他在這個國際研討會上發表了演講。",
                "difficulty_level": 4,
                "related_category": "Academic"
            },
            {
                "word": "synthesis",
                "part_of_speech": "n",
                "translation": "綜合體；綜合",
                "pronunciation": "/ˈsɪnθəsɪs/",
                "example_sentence": "The new theory is a synthesis of several earlier ideas.",
                "example_translation": "這個新理論是幾種早期想法的綜合。",
                "difficulty_level": 5,
                "related_category": "Academic"
            },
            {
                "word": "system",
                "part_of_speech": "n",
                "translation": "制度；體制",
                "pronunciation": "/ˈsɪstəm/",
                "example_sentence": "The new system is much more efficient.",
                "example_translation": "這個新系統效率更高。",
                "difficulty_level": 1,
                "related_category": "Technology"
            },
            {
                "word": "systematically",
                "part_of_speech": "adv.",
                "translation": "有系統地；有組織地",
                "pronunciation": "/ˌsɪstəˈmætɪkli/",
                "example_sentence": "He systematically analyzed all the data.",
                "example_translation": "他有系統地分析了所有數據。",
                "difficulty_level": 3,
                "related_category": "Academic"
            },
            {
                "word": "table",
                "part_of_speech": "n",
                "translation": "桌子；表格",
                "pronunciation": "/ˈteɪbl/",
                "example_sentence": "Please put the books on the table.",
                "example_translation": "請把書放在桌子上。",
                "difficulty_level": 1,
                "related_category": "DailyLife"
            },
            {
                "word": "tactic",
                "part_of_speech": "n",
                "translation": "策略；戰術",
                "pronunciation": "/ˈtæktɪk/",
                "example_sentence": "The marketing team's new tactic increased sales.",
                "example_translation": "行銷團隊的新策略提升了銷售額。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "takeover",
                "part_of_speech": "n",
                "translation": "接管；收購",
                "pronunciation": "/ˈteɪkˌoʊvər/",
                "example_sentence": "The company announced a hostile takeover of its competitor.",
                "example_translation": "這家公司宣布對其競爭對手進行惡意收購。",
                "difficulty_level": 4,
                "related_category": "Business"
            },
            {
                "word": "technical",
                "part_of_speech": "adj.",
                "translation": "技術的；專業的",
                "pronunciation": "/ˈteknɪkəl/",
                "example_sentence": "He has a lot of technical knowledge about computers.",
                "example_translation": "他對電腦有許多專業知識。",
                "difficulty_level": 2,
                "related_category": "Technology"
            },
            {
                "word": "technology",
                "part_of_speech": "n",
                "translation": "技術；科技",
                "pronunciation": "/tekˈnɑːlədʒi/",
                "example_sentence": "The latest technology allows us to communicate instantly.",
                "example_translation": "最新的科技使我們能夠即時通訊。",
                "difficulty_level": 1,
                "related_category": "Technology"
            },
            {
                "word": "teleconference",
                "part_of_speech": "n",
                "translation": "電話會議",
                "pronunciation": "/ˈtelɪˌkɑːnfərəns/",
                "example_sentence": "We had a teleconference with the team in Japan.",
                "example_translation": "我們和日本的團隊開了電話會議。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "terminal",
                "part_of_speech": "n, adj.",
                "translation": "終點站；航廈 (n)；末端的；最終的 (adj.)",
                "pronunciation": "/ˈtɜːrmɪnl/",
                "example_sentence": "We arrived at Terminal 2 for our flight.",
                "example_translation": "我們抵達第二航廈搭機。",
                "difficulty_level": 2,
                "related_category": "Travel"
            },
            {
                "word": "telecommute",
                "part_of_speech": "v",
                "translation": "遠距辦公",
                "pronunciation": "/ˌtelɪkəˈmjuːt/",
                "example_sentence": "Many employees are choosing to telecommute from home.",
                "example_translation": "許多員工選擇在家遠距辦公。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "trademark",
                "part_of_speech": "n",
                "translation": "商標",
                "pronunciation": "/ˈtreɪdmɑːrk/",
                "example_sentence": "The company's logo is a registered trademark.",
                "example_translation": "這家公司的標誌是註冊商標。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "transparent",
                "part_of_speech": "adj.",
                "translation": "透明的；公開的",
                "pronunciation": "/trænsˈpærənt/",
                "example_sentence": "The company's financial records are completely transparent.",
                "example_translation": "公司的財務記錄完全公開透明。",
                "difficulty_level": 3,
                "related_category": "Business"
            },
            {
                "word": "template",
                "part_of_speech": "n",
                "translation": "模板；樣板",
                "pronunciation": "/ˈtemplət/",
                "example_sentence": "You can use this template for your presentation.",
                "example_translation": "您可以使用這個模板來製作您的簡報。",
                "difficulty_level": 2,
                "related_category": "Technology"
            },
            {
                "word": "tool",
                "part_of_speech": "n",
                "translation": "工具；手段",
                "pronunciation": "/tuːl/",
                "example_sentence": "This new software is a very useful tool for data analysis.",
                "example_translation": "這個新軟體是個非常有用的數據分析工具。",
                "difficulty_level": 1,
                "related_category": "Technology"
            },
            {
                "word": "transaction",
                "part_of_speech": "n",
                "translation": "交易；業務",
                "pronunciation": "/trænˈzækʃən/",
                "example_sentence": "All transactions are recorded in the ledger.",
                "example_translation": "所有交易都記錄在總帳中。",
                "difficulty_level": 2,
                "related_category": "Business"
            },
            {
                "word": "troubleshoot",
                "part_of_speech": "v",
                "translation": "解決故障；排解疑難",
                "pronunciation": "/ˈtrʌblˌʃuːt/",
                "example_sentence": "He spent all morning trying to troubleshoot the network problem.",
                "example_translation": "他整個上午都在試圖解決網路問題。",
                "difficulty_level": 3,
                "related_category": "Technology"
            },
            {
                "word": "tutorial",
                "part_of_speech": "n",
                "translation": "教學課程；指導",
                "pronunciation": "/tuːˈtɔːriəl/",
                "example_sentence": "I watched a video tutorial to learn how to use the app.",
                "example_translation": "我看了一段影片教學來學習如何使用這個應用程式。",
                "difficulty_level": 2,
                "related_category": "Technology"
            }
        ]
        
        self.stdout.write(self.style.NOTICE('開始匯入商業與人力資源相關單字資料...'))
        
        for word_data in words_to_import:
            # 清理單字，移除括號內的內容
            cleaned_word = re.sub(r'（.*|\(.*\)', '', word_data['word']).strip()
            
            try:
                DailyVocabulary.objects.update_or_create(
                    word=cleaned_word,
                    defaults={
                        "part_of_speech": word_data.get("part_of_speech", ""),
                        "translation": word_data.get("translation", ""),
                        "pronunciation": word_data.get("pronunciation", ""),
                        "example_sentence": word_data.get("example_sentence", ""),
                        "example_translation": word_data.get("example_translation", ""),
                        "difficulty_level": word_data.get("difficulty_level", 1),
                        "related_category": word_data.get("related_category", "Uncategorized")
                    }
                )
                self.stdout.write(self.style.SUCCESS(f"成功處理單字: {cleaned_word}"))
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f"單字 {cleaned_word} 已存在，跳過。"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"新增單字 {cleaned_word} 時出錯: {e}"))
                
        self.stdout.write(self.style.SUCCESS('所有單字處理完畢！'))
