FROM python:3.11

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip
RUN pip install --upgrade pip setuptools wheel

# 複製 requirements.txt 並安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有其他程式碼
COPY . .

# 啟動 FastAPI
CMD ["uvicorn", "api_part2:app", "--host", "0.0.0.0", "--port", "11432"]
