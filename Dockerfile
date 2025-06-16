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
CMD ["python", "-m", "functions_framework", "--target=main", "--port=8080"]