# 📅 K-POP Schedule Auto-Feed

> 公式 X と Web 検索からスケジュールを収集し、AI で抽出 → Google カレンダーに自動反映する Cloud Run アプリ

## ✨ ユースケース
1. 推しアカをフォームで登録  
2. Cloud Scheduler が毎日 4:00 JST に収集  
3. Gemini で「日付・タイトル・種別」を抽出  
4. Google Calendar へ登録（ICS も配布）

## 🔧 技術スタック
| 区分 | 採用技術 |
|------|----------|
| フロント | FastAPI + HTMX |
| バックエンド | Python 3.11 / Functions Framework |
| サーバレス | Cloud Run (2nd gen) / Scheduler |
| 生成 AI | Vertex AI Gemini Pro |
| スクレイピング | snscrape / SerpAPI |
| データ | Firestore |
| CI/CD | GitHub Actions → gcloud run deploy |

## 📂 構成
schedule/               ← このGitHubリポジトリ
├── README.md           ← プロジェクト概要（Claudeが生成可）
├── src/                ← バックエンドPythonコード（Cloud Run用）
│   ├── scraper.py      ← snscrapeを使ったX収集
│   ├── search.py       ← Web検索 & HTML抽出処理
│   ├── extractor.py    ← Geminiでイベント抽出
│   ├── calendar.py     ← Google Calendar連携（またはICS）
│   ├── register.py     ← 推し登録用 FastAPI ミニUI
│   └── main.py         ← 全処理の起点関数(run_allなど)
├── requirements.txt    ← 必要ライブラリ（Claudeが補完）
├── deploy.sh           ← 手動デプロイスクリプト
├── .github/
│   └── workflows/
│       └── deploy.yml  ← GitHub Actionsによる自動デプロイ
├── cloudbuild.yaml     ← 任意：Cloud Buildトリガー用（自動化に使うなら）
└── docs/               ← すでにあるソース一覧やREADME補足など
