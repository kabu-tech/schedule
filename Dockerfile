# K-POP Schedule Auto-Feed Dockerfile

FROM python:3.11-slim

WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート設定
EXPOSE 8080

# アプリケーション実行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]