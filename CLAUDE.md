# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

K-POP Schedule Auto-Feed - K-POPアーティストのスケジュール情報を自動収集してGoogleカレンダーに反映するCloud Runアプリケーション

### 技術スタック
- **バックエンド**: Python 3.11, FastAPI, Functions Framework
- **インフラ**: Google Cloud Run (2nd gen), Cloud Scheduler, Firestore
- **AI/ML**: Vertex AI Gemini Pro（スケジュール情報抽出）
- **スクレイピング**: snscrape（X/Twitter）、SerpAPI（Web検索）
- **日本語処理**: jaconv, mojimoji

### 重要なドキュメント
- **setup.md**: 初心者向けの詳細なセットアップガイド
- **docs/local-test.md**: ローカル環境での動作確認手順
- **docs/02_sources.md**: データソース一覧

## 開発コマンド

### 環境構築
```bash
# Python仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### ローカル開発
```bash
# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# FastAPIサーバーの起動（開発モード）
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# または、プロジェクトルートから
PYTHONPATH=./src uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

詳細な動作確認手順は `docs/local-test.md` を参照。

### コード品質
```bash
# フォーマット
black src/

# リンティング
flake8 src/

# 型チェック
mypy src/
```

### デプロイ
```bash
# 手動デプロイ（deploy.shを使用）
chmod +x deploy.sh
./deploy.sh

# または直接gcloudコマンド
gcloud run deploy schedule-auto-feed \
  --source=. \
  --platform=managed \
  --region=asia-northeast1 \
  --allow-unauthenticated
```

## アーキテクチャ

### ディレクトリ構造
```
src/
├── main.py         # Cloud Runエントリポイント（未実装）
├── config.py       # 日本語設定とプロンプトテンプレート
├── scraper.py      # X (Twitter)スクレイピング処理
├── extractor.py    # Vertex AI Geminiによるスケジュール抽出
├── calendar.py     # Google Calendar連携（未実装）
├── register.py     # 推しアイドル登録UI（未実装）
└── utils/
    └── japanese.py # 日本語テキスト処理ユーティリティ
```

### 主要モジュールの概要

#### scraper.py
- `XScraper`クラス: snscrapeを使用したX投稿取得
- 日本語対応済み、リトライ処理、エラーハンドリング実装
- 主要メソッド: `search_tweets()`, `get_user_tweets()`, `extract_schedule_candidates()`

#### extractor.py
- `ScheduleExtractor`クラス: Vertex AI Geminiによるスケジュール情報抽出
- 日本語プロンプト使用、構造化データ抽出
- 主要メソッド: `extract_from_text()`, `extract_from_multiple_sources()`, `validate_and_normalize()`

#### utils/japanese.py
- 日本語日付・時刻の抽出と正規化
- 全角・半角変換、テキスト正規化
- イベント種別の自動判定

## 日本語対応

プロジェクト全体で日本語に完全対応：
- UTF-8エンコーディング統一
- 日本語ロケール設定（Asia/Tokyo）
- 日本語プロンプトテンプレート（src/config.py）
- 日本語日付形式の自動認識（例: "2024年1月15日"）
- イベント種別の日本語対応（コンサート、リリース、テレビ出演など）

## 実装状況

### 実装済み ✅
- X (Twitter)スクレイピング機能
- Vertex AI Geminiによるスケジュール抽出
- 日本語処理ユーティリティ
- 設定ファイルとプロンプトテンプレート
- main.py: FastAPIアプリケーションの基本実装（ヘルスチェック、テストエンドポイント）

### 未実装 ⏳
- calendar.py: Google Calendar API連携
- register.py: アイドル登録用Web UI
- Firestore連携（アーティスト情報の保存/取得）
- 本番用のスケジュール収集処理
- テストコード
- CI/CD（GitHub Actions）

## 開発時の注意点

1. **API キー管理**: 必ず環境変数で管理し、コミットしない
2. **日本語処理**: すべてのテキスト処理で`utils/japanese.py`を使用
3. **エラーハンドリング**: スクレイピング失敗時の適切なフォールバック
4. **レート制限**: 外部API使用時は適切な遅延とリトライを実装
5. **ログ出力**: 日本語でのログ出力を維持
