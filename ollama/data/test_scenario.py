from sentence_transformers import SentenceTransformer
import chromadb

# 初始化模型與 ChromaDB
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="C:/Users/Fyn/Desktop/rag/chroma_db")
collection = chroma_client.get_or_create_collection("toeic_scenarios")

# 定義測驗情境資料
toeic_scenarios = [
    {"情境": "企業發展", "內容": "研究、產品研發"},
    {"情境": "外食", "內容": "商務／非正式午餐、宴會、招待會、餐廳訂位"},
    {"情境": "娛樂", "內容": "電影、劇場、音樂、藝術、展覽、博物館、媒體"},
    {"情境": "金融／預算", "內容": "銀行業務、投資、稅務、會計、帳單"},
    {"情境": "一般商務", "內容": "契約、談判、併購、行銷、銷售、保證、商業企劃、會議、勞動關係"},
    {"情境": "保健", "內容": "醫療保險、看醫生、牙醫、診所、醫院"},
    {"情境": "房屋／公司地產", "內容": "建築、規格、購買租賃、電力瓦斯服務"},
    {"情境": "製造業", "內容": "工廠管理、生產線、品管"},
    {"情境": "辦公室", "內容": "董事會、委員會、信件、備忘錄、電話、傳真、電子郵件、辦公室器材與家具、辦公室流程"},
    {"情境": "人事", "內容": "招考、雇用、退休、薪資、升遷、應徵與廣告、津貼、獎勵"},
    {"情境": "採購", "內容": "購物、訂購物資、送貨、發票"},
    {"情境": "技術層面", "內容": "電子、科技、電腦、實驗室與相關器材、技術規格"},
    {"情境": "旅遊", "內容": "火車、飛機、計程車、巴士、船隻、渡輪、票務、時刻表、車站、機場廣播、租車、飯店、預定、脫班與取消"},
]

# 將資料轉為向量並上傳至 ChromaDB
for scenario in toeic_scenarios:
    text = f"{scenario['情境']}：{scenario['內容']}"
    embedding = embedding_model.encode(text)
    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[scenario["情境"]]
    )
