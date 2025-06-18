# 🧪 ローカル動作確認ガイド

このガイドでは、開発環境でアプリケーションを動作確認する手順を説明します。

## 前提条件

- setup.mdの手順が完了していること
- Python仮想環境が有効化されていること
- .envファイルが設定済みであること

## 1. 依存関係の確認

```bash
# 仮想環境が有効か確認
which python
# 出力例: /Users/yourname/schedule/.venv/bin/python

# 必要なパッケージがインストールされているか確認
pip list | grep -E "fastapi|uvicorn|snscrape|vertexai"
```

## 2. 環境変数の確認

```bash
# .envファイルの存在確認
ls -la .env

# 必要な環境変数が設定されているか確認（キーの値は表示しない）
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('GOOGLE_CLOUD_PROJECT:', bool(os.getenv('GOOGLE_CLOUD_PROJECT')))
print('GOOGLE_APPLICATION_CREDENTIALS:', bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')))
print('SERPAPI_KEY:', bool(os.getenv('SERPAPI_KEY')))
"
```

## 3. FastAPIサーバーの起動

### 基本的な起動方法

```bash
# srcディレクトリから起動
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 起動成功時の表示例

```
INFO:     Will watch for changes in these directories: ['/Users/yourname/schedule/src']
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 4. 基本的な動作確認

### 4.1 ブラウザでの確認

以下のURLにアクセス：

- **ホームページ**: http://localhost:8080
  - APIの基本情報が表示される
  
- **API仕様書（Swagger UI）**: http://localhost:8080/docs
  - 対話的にAPIをテストできる
  
- **代替API仕様書（ReDoc）**: http://localhost:8080/redoc
  - より詳細なドキュメント

### 4.2 コマンドラインでの確認

```bash
# ヘルスチェック
curl http://localhost:8080/health | python -m json.tool

# 期待される応答例：
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00+09:00",
    "version": "0.1.0",
    "services": {
        "api": "healthy",
        "scraper": "healthy",
        "extractor": "healthy",
        "calendar": "not_implemented",
        "database": "not_connected"
    }
}
```

## 5. 機能別テスト

### 5.1 スクレイピング機能のテスト（モック）

```bash
# X (Twitter)スクレイピングのテスト
curl -X POST http://localhost:8080/test/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "NewJeans schedule",
    "source": "twitter",
    "limit": 5
  }' | python -m json.tool
```

**注意**: 実際のスクレイピングにはAPIキーが必要です。エラーが出る場合は以下を確認：
- snscrapeの設定
- ネットワーク接続
- レート制限

### 5.2 エラーハンドリングの確認

```bash
# 存在しないエンドポイント
curl http://localhost:8080/notfound
# 期待: 404エラー

# 不正なリクエスト
curl -X POST http://localhost:8080/test/scrape \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
# 期待: 422 Validation Error
```

## 6. ログの確認

サーバー起動時のターミナルに以下のようなログが表示されます：

```
INFO:     127.0.0.1:50123 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:50124 - "GET /health HTTP/1.1" 200 OK
INFO:     Test scrape request: NewJeans schedule
```

## 7. トラブルシューティング

### よくある問題と解決方法

#### ImportError: No module named 'XXX'

```bash
# 解決方法
pip install -r requirements.txt
```

#### scraper.pyやextractor.pyのインポートエラー

```bash
# PYTHONPATHを設定
export PYTHONPATH="${PYTHONPATH}:/Users/yourname/schedule/src"

# または、srcディレクトリから実行
cd src && uvicorn main:app --reload
```

#### Google Cloud認証エラー

```bash
# 認証情報ファイルの存在確認
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# 権限確認
gcloud auth application-default print-access-token
```

#### ポート8080が使用中

```bash
# 使用中のプロセスを確認
lsof -i :8080

# 別のポートで起動
uvicorn main:app --reload --port 8081
```

## 8. 開発時の便利なコマンド

```bash
# ログレベルを変更して詳細表示
uvicorn main:app --reload --log-level debug

# 特定のホストからのみアクセス許可
uvicorn main:app --reload --host 127.0.0.1

# HTTPSで起動（証明書が必要）
uvicorn main:app --reload --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

## 9. 次のステップ

ローカルでの動作確認が完了したら：

1. **単体テストの作成**: `pytest`を使用したテスト
2. **統合テスト**: 実際のAPIとの連携テスト
3. **パフォーマンステスト**: 負荷テストツールでの確認
4. **Cloud Runへのデプロイ**: `deploy.sh`を使用

## 補足：VSCodeでのデバッグ

`.vscode/launch.json`を作成：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "src.main:app",
                "--reload"
            ],
            "jinja": true,
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

これでVSCodeからデバッグ実行が可能になります。