# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

K-POP Schedule Auto-Feed - K-POPアーティストのスケジュール情報を自動収集してGoogleカレンダーに反映するCloud Runアプリケーション

**🚀 本番環境URL:** https://schedule-auto-feed-wkwgupze5a-an.a.run.app

### 技術スタック
- **バックエンド**: Python 3.11, FastAPI
- **インフラ**: Google Cloud Run, Artifact Registry, Firestore
- **CI/CD**: GitHub Actions (Workload Identity Federation)
- **AI/ML**: Gemini API（スケジュール情報抽出・信頼性フィルタリング）
- **検索・情報収集**: Google Programmable Search Engine API（Web検索）
- **認証**: Workload Identity Federation（セキュア認証）

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
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# または、プロジェクトルートから
PYTHONPATH=./app uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### テスト実行
```bash
# 全テスト実行
pytest

# 特定のテストファイル実行
pytest tests/test_sources.py -v
pytest tests/test_extract.py -v
pytest tests/test_events_save.py -v
```

### コード品質
```bash
# フォーマット
black app/

# リンティング
flake8 app/

# 型チェック
mypy app/
```

### デプロイ
```bash
# 自動デプロイ（GitHub Actions）
git push origin main  # mainブランチへのpushで自動デプロイ

# 手動デプロイ（ローカルから）
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
- `WebSearchScraper`クラス: Google Programmable Search Engine APIを使用したWeb検索
- 信頼性の高い情報源からのスケジュール情報収集
- 日本語対応済み、リトライ処理、エラーハンドリング実装
- 主要メソッド: `search_web()`, `filter_reliable_sources()`, `extract_schedule_candidates()`

#### extractor.py
- `ScheduleExtractor`クラス: Vertex AI Geminiによるスケジュール情報抽出
- **改良版プロンプト**: 信頼性フィルタリング機能付き日本語プロンプト
- 構造化データ抽出、情報源品質評価、重複排除
- 主要メソッド: `extract_from_text()`, `extract_from_multiple_sources()`, `validate_and_normalize()`, `filter_by_reliability()`

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
- ~~X (Twitter)スクレイピング機能~~（廃止：法的リスク・安定性の問題）
- **Google Programmable Search Engine API連携**（新規：2025-06-18 Issue #9で評価・決定）
- **改良版Gemini信頼性フィルタリング機能**（新規：2025-06-18 Issue #9で設計・評価）
- Vertex AI Geminiによるスケジュール抽出
- 日本語処理ユーティリティ
- 設定ファイルとプロンプトテンプレート
- main.py: FastAPIアプリケーションの基本実装（ヘルスチェック、テストエンドポイント）
- calendar.py: Google Calendar API連携

### 未実装 ⏳
- register.py: アイドル登録用Web UI
- Firestore連携（アーティスト情報の保存/取得）
- 本番用のスケジュール収集処理
- テストコード
- CI/CD（GitHub Actions）

## アーキテクチャ設計変更履歴

### 📋 Issue #9: 検索要件の変更（2025-06-18）

#### 🔄 主要な設計変更

| 変更項目 | 旧方式 | 新方式 | 決定理由 |
|----------|--------|--------|----------|
| **情報収集** | snscrape（X/Twitter） | Google Programmable Search API | ✅ 法的リスク回避、安定性向上 |
| **対象範囲** | X投稿のみ | Web全体（公式サイト、メディア等） | ✅ 情報源多様化、品質向上 |
| **抽出処理** | 基本的なGemini抽出 | 信頼性フィルタリング付きGemini | ✅ 情報品質の大幅向上 |
| **商用適合性** | 規約違反リスク | 正規API使用で商用OK | ✅ ハッカソン・商用展開対応 |

#### 🤖 Geminiプロンプト改良

**改良前の課題**:
- 情報源の信頼性判定なし
- Web検索結果への対応不足
- 情報品質フィルタリング機能なし

**改良後の特徴**:
- **信頼性基準の明確化**: 公式サイト・大手メディア・チケットサイト等を優先
- **除外パターンの定義**: 個人ブログ・噂・未確認情報を自動除外
- **品質指標の追加**: `confidence`（0.0-1.0）、`reliability`（high/medium/low）
- **重複処理機能**: 複数ソースからの同一情報を統合

#### 📊 技術的評価結果

**利点 ✅**:
- 法的リスク: 高 → 低（正規API使用）
- 安定性: 低 → 高（公式サポート）
- 情報量: 中 → 高（Web全体）
- 商用適合性: 不可 → 可能

**制約 ⚠️**:
- コスト: 無料 → 有料（月100クエリまで無料）
- 実装難易度: 易 → 中（品質管理機能追加）

#### 🎯 実装方針

1. **段階的移行**: 既存snscrape実装と並行運用で比較評価
2. **品質管理**: 信頼できるドメインのホワイトリスト管理
3. **コスト最適化**: APIクエリ使用量監視とキャッシュ機能
4. **フォールバック**: API障害時の代替データソース準備

---

## 開発時の注意点

1. **API キー管理**: 必ず環境変数で管理し、コミットしない
2. **日本語処理**: すべてのテキスト処理で`utils/japanese.py`を使用
3. **エラーハンドリング**: API失敗時の適切なフォールバック
4. **レート制限**: 外部API使用時は適切な遅延とリトライを実装
5. **情報品質管理**: 信頼性フィルタリング機能の活用
6. **コスト監視**: Google Search API使用量の定期的な確認
7. **ログ出力**: 日本語でのログ出力を維持

## Geminiプロンプト設計ガイドライン

### 🎯 信頼性重視の抽出プロンプト

```text
以下の検索結果から、信頼性の高いK-POPスケジュール情報のみを抽出してください。

【信頼性判定基準】
高信頼度：
- 公式サイト（.com、.jp、.kr等で「official」「artist名」を含むドメイン）
- 大手メディア（NHK、朝日新聞、音楽ナタリーなど）
- 公式チケットサイト（e+、チケットぴあ、ローソンチケットなど）
- 行政機関の発表

低信頼度（無視する）：
- 個人ブログ・まとめサイト
- 「〜かも」「〜らしい」「噂」「予想」を含む投稿
- 匿名掲示板・SNSの非公式投稿
- 「未確認」「リーク」を含む情報

【抽出ルール】
1. 明確な日付が記載されているもののみ
2. 過去の日付は除外
3. 信頼度0.7未満の情報は除外
4. 重複する情報は信頼度の高いものを優先

【出力形式】
```json
{
    "events": [
        {
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "アーティスト名", 
            "type": "コンサート|リリース|テレビ出演|ラジオ出演|イベント|その他",
            "location": "開催場所",
            "source": "https://...",
            "confidence": 0.9,
            "reliability": "high|medium|low"
        }
    ]
}
```

信頼性が低い場合は結果を空の配列で返してください。
```

### 🔧 プロンプト設計のポイント

1. **具体的な判定基準**: ドメイン例と除外パターンを明示
2. **構造化された出力**: 既存システムとの互換性確保
3. **品質指標の組み込み**: `confidence`と`reliability`による品質管理
4. **重複処理の指示**: 検索結果特有の重複問題に対応
5. **閾値の設定**: 数値基準による一貫した品質判定
