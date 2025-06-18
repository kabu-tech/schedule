# 📚 K-POP Schedule Auto-Feed セットアップガイド

このガイドでは、プロジェクトを始めるために必要な設定を初心者向けに説明します。

## 📋 目次
1. [事前準備](#事前準備)
2. [Google Cloud の設定](#google-cloud-の設定)
3. [APIキーの取得](#apiキーの取得)
4. [ローカル開発環境の構築](#ローカル開発環境の構築)
5. [動作確認](#動作確認)
6. [トラブルシューティング](#トラブルシューティング)

## 事前準備

### 必要なアカウント
- [ ] Googleアカウント（Google Cloud用）
- [ ] GitHubアカウント（ソースコード管理用）
- [ ] SerpAPIアカウント（Web検索用）※無料プランでOK

### 必要なソフトウェア
- [ ] Python 3.11以上
- [ ] Git
- [ ] テキストエディタ（VS Code推奨）

## Google Cloud の設定

### 1. Google Cloud プロジェクトの作成

1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. 右上の「プロジェクトを選択」→「新しいプロジェクト」をクリック
3. プロジェクト情報を入力：
   - プロジェクト名: `kpop-schedule-feed`（任意）
   - プロジェクトID: 自動生成されたものをメモ（後で使用）
4. 「作成」をクリック

### 2. 必要なAPIの有効化

Google Cloud Consoleで以下のAPIを有効化します：

```bash
# gcloud CLIを使う場合（推奨）
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable calendar-json.googleapis.com
```

または、Cloud Consoleから手動で有効化：
1. 左メニュー → 「APIとサービス」→「ライブラリ」
2. 以下を検索して有効化：
   - Cloud Run API
   - Cloud Scheduler API
   - Cloud Firestore API
   - Vertex AI API
   - Google Calendar API

### 3. サービスアカウントの作成

1. Cloud Console → 「IAMと管理」→「サービスアカウント」
2. 「サービスアカウントを作成」をクリック
3. 以下を入力：
   - サービスアカウント名: `schedule-feed-sa`
   - サービスアカウントID: 自動生成でOK
4. 「作成して続行」をクリック
5. 以下のロールを付与：
   - Cloud Run 開発者
   - Cloud Scheduler 管理者
   - Cloud Datastore ユーザー
   - Vertex AI ユーザー
6. 「完了」をクリック

### 4. サービスアカウントキーの作成

1. 作成したサービスアカウントをクリック
2. 「キー」タブ → 「鍵を追加」→「新しい鍵を作成」
3. 「JSON」を選択して「作成」
4. ダウンロードされたJSONファイルを安全な場所に保存
   - ファイル名例: `schedule-feed-sa-key.json`
   - **重要**: このファイルは絶対にGitにコミットしないこと！

### 5. gcloud CLIのインストールと設定

1. [gcloud CLI](https://cloud.google.com/sdk/docs/install) をインストール
2. 初期設定：
```bash
# ログイン
gcloud auth login

# プロジェクトの設定
gcloud config set project YOUR_PROJECT_ID  # 手順1でメモしたプロジェクトID

# デフォルトリージョンの設定
gcloud config set run/region asia-northeast1
```

## APIキーの取得

### SerpAPI（Web検索用）

1. [SerpAPI](https://serpapi.com) にアクセス
2. 無料アカウントを作成（月100回まで無料）
3. ダッシュボードからAPIキーをコピー

### Vertex AI（Gemini）の設定

Vertex AIはGoogle Cloud内で利用するため、追加のAPIキーは不要です。
サービスアカウントの認証情報で自動的に利用できます。

## ローカル開発環境の構築

### 1. リポジトリのクローン

```bash
git clone https://github.com/YOUR_USERNAME/schedule.git
cd schedule
```

### 2. Python仮想環境の作成

```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# Mac/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# .envファイルの作成
cp .env.example .env
```

`.env`ファイルを編集：
```env
# Google Cloud設定
GOOGLE_CLOUD_PROJECT=your-project-id  # 手順1でメモしたプロジェクトID
GOOGLE_APPLICATION_CREDENTIALS=path/to/schedule-feed-sa-key.json  # 手順4で保存したファイルパス

# API設定
SERPAPI_KEY=your-serpapi-key  # SerpAPIのキー

# その他の設定はそのままでOK
```

### 4. Firestoreの初期設定

1. Cloud Console → 「Firestore」
2. 「データベースを作成」をクリック
3. 「ネイティブモード」を選択
4. ロケーション: `asia-northeast1`（東京）を選択
5. 「作成」をクリック

## 動作確認

### 1. FastAPIサーバーの起動

```bash
# 開発サーバーの起動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### 2. ブラウザでアクセス

- アプリケーション: http://localhost:8080
- API仕様書: http://localhost:8080/docs

### 3. 基本機能のテスト

```bash
# ヘルスチェック
curl http://localhost:8080/health

# スクレイピングのテスト（例）
curl -X POST http://localhost:8080/test/scrape \
  -H "Content-Type: application/json" \
  -d '{"query": "NewJeans schedule"}'
```

## トラブルシューティング

### よくあるエラーと対処法

#### 1. ModuleNotFoundError
```
エラー: ModuleNotFoundError: No module named 'fastapi'
対処: pip install -r requirements.txt を実行
```

#### 2. Google Cloud認証エラー
```
エラー: Could not automatically determine credentials
対処: 
1. GOOGLE_APPLICATION_CREDENTIALS が正しく設定されているか確認
2. JSONファイルのパスが正しいか確認
3. 絶対パスで指定してみる
```

#### 3. ポート使用中エラー
```
エラー: [Errno 48] Address already in use
対処: 
1. 別のポートを使用: --port 8081
2. または既存のプロセスを終了
```

### デバッグモード

開発時は以下の設定でデバッグ情報を表示：
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 次のステップ

基本設定が完了したら：
1. `docs/development.md` - 開発の進め方
2. `docs/deployment.md` - Cloud Runへのデプロイ方法
3. `docs/02_sources.md` - データソースの追加方法

## サポート

問題が解決しない場合：
- GitHubのIssuesに質問を投稿
- より詳細なログを確認: `uvicorn --log-level debug`