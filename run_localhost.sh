#!/bin/bash
# K-POP Schedule Auto-Feed ローカル開発用起動スクリプト

echo "🚀 K-POP Schedule Auto-Feed を起動中..."

# 仮想環境の確認・有効化
if [ ! -d ".venv" ]; then
    echo "❌ 仮想環境が見つかりません。作成します..."
    python -m venv .venv
fi

source .venv/bin/activate

# 基本パッケージのインストール
echo "📦 基本パッケージをインストール中..."
pip install fastapi uvicorn[standard] pydantic python-dotenv --quiet

# 環境変数の設定
if [ ! -f ".env" ]; then
    echo "⚠️  .envファイルを作成中..."
    cp .env.example .env
fi

# 環境変数の読み込み
export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true

echo "🌐 サーバーを起動中..."
echo "📍 URL: http://localhost:8000"
echo "📚 API仕様書: http://localhost:8000/docs"
echo "🔧 ヘルスチェック: http://localhost:8000/health"
echo ""

cd app && uvicorn main:app --reload --host 127.0.0.1 --port 8000