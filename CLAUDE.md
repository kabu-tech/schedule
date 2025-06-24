# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

**Universal Entertainment Schedule Auto-Feed** - あらゆるジャンル（K-POP、J-POP、演劇等）のアーティスト・エンターテイメント情報を自動収集してGoogleカレンダーに反映する汎用Cloud Runアプリケーション

🎯 **2025-06-24 大幅アップデート**: K-POP専用システムから**汎用エンターテイメント情報収集システム**に進化

**🚀 本番環境URL:** https://schedule-auto-feed-wkwgupze5a-an.a.run.app

### 技術スタック
- **バックエンド**: Python 3.11, FastAPI
- **インフラ**: Google Cloud Run, Artifact Registry, Firestore
- **CI/CD**: GitHub Actions (Workload Identity Federation)
- **AI/ML**: Gemini API（汎用ジャンル対応スケジュール抽出・AI信頼性フィルタリング）
- **検索・情報収集**: Google Programmable Search Engine API（制限なし汎用Web検索）
- **認証**: Workload Identity Federation（セキュア認証）

### 🌟 新機能（2025-06-24）
- **🎭 汎用ジャンル対応**: K-POP、J-POP、J-ROCK、演劇、クラシックなど全ジャンル
- **🤖 AI信頼性判定**: Geminiによる自動的な情報源品質評価とフィルタリング
- **🌐 制限なし検索**: Web全体を対象とした汎用検索エンジン
- **📊 100%拡張性**: 新しいジャンルへの即座対応（実証済み）

### 重要なドキュメント
- **setup.md**: 初心者向けの詳細なセットアップガイド
- **docs/local-test.md**: ローカル環境での動作確認手順
- **docs/improved-search-strategy.md**: 汎用検索+AI信頼性判定アプローチ
- **docs/create-universal-search-engine.md**: 汎用検索エンジン設定手順
- **docs/kpop-reliable-sources.md**: 信頼できる情報源リスト

### テスト・開発ツール
- **scripts/test-universal-search.py**: 汎用ジャンル対応テストスクリプト
- **scripts/test-search-engine.py**: 検索エンジン動作確認スクリプト

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

# 汎用検索システムのテスト（2025-06-24新規）
python scripts/test-universal-search.py     # 複数ジャンルでの動作確認
python scripts/test-search-engine.py        # 検索エンジン基本動作確認
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
app/
├── main.py                    # Cloud Run FastAPIエントリポイント ✅
├── config.py                  # 汎用ジャンル対応プロンプトテンプレート ✅
├── routers/
│   ├── artists.py            # アーティスト登録API ✅
│   ├── schedules.py          # 汎用スケジュール収集API ✅
│   └── extract.py            # Gemini抽出API ✅
├── services/
│   ├── schedule_collector.py # 汎用検索+AI信頼性判定システム ✅
│   ├── firestore_client.py   # Firestore連携サービス ✅
│   └── register.py           # アーティスト登録サービス ✅
├── utils/
│   └── japanese.py          # 日本語テキスト処理ユーティリティ ✅
└── templates/
    └── artists.html         # アーティスト登録UI ✅

docs/                        # 📚 2025-06-24 大幅拡充
├── improved-search-strategy.md     # 汎用検索戦略
├── create-universal-search-engine.md  # 設定手順
└── kpop-reliable-sources.md        # 信頼できる情報源

scripts/                     # 🧪 2025-06-24 新規追加
├── test-universal-search.py        # 汎用ジャンルテスト
└── test-search-engine.py          # 検索エンジンテスト
```

### 🎯 主要モジュールの概要（2025-06-24 大幅アップデート）

#### 🌟 services/schedule_collector.py（新システムの中核）
- `ScheduleCollector`クラス: **汎用ジャンル対応**スケジュール収集システム
- **Google Search API + Gemini AI**の完全統合
- **ジャンル横断対応**: K-POP、J-POP、J-ROCK、演劇、クラシック等
- **AI信頼性フィルタリング**: 自動的な情報源品質評価
- 主要メソッド: `collect_artist_schedules(genre)`, `_extract_schedules_with_gemini()`, `_validate_and_normalize_events()`

#### 🎭 config.py（汎用プロンプトテンプレート）
- **UNIVERSAL_SCHEDULE_PROMPT_TEMPLATE**: あらゆるジャンル対応プロンプト
- **AI信頼性判定基準**: 公式サイト・大手メディア・チケットサイト優先
- **除外パターン**: 個人ブログ・噂・未確認情報を自動除外
- **品質指標**: `confidence`（0.0-1.0）、`reliability`（high/medium/low）、`genre`

#### 🗄️ services/firestore_client.py
- Firestore database連携とアーティスト情報永続化
- ヘルスチェック機能、エラーハンドリング
- アーティスト登録・取得・更新の完全サポート

#### 🎨 services/register.py & routers/artists.py
- アーティスト登録システム（Web UI + API）
- Firestore連携によるデータ永続化
- 日本語正規化とバリデーション機能

#### 🛠️ utils/japanese.py
- 日本語日付・時刻の抽出と正規化（`normalize_date()`, `normalize_time()`）
- 全角・半角変換、テキスト正規化
- イベント種別の自動判定

## 日本語対応

プロジェクト全体で日本語に完全対応：
- UTF-8エンコーディング統一
- 日本語ロケール設定（Asia/Tokyo）
- 日本語プロンプトテンプレート（src/config.py）
- 日本語日付形式の自動認識（例: "2024年1月15日"）
- イベント種別の日本語対応（コンサート、リリース、テレビ出演など）

## 🎯 実装状況（2025-06-24 アップデート）

### ✅ 実装済み（フル機能）
- **🌟 汎用ジャンル対応システム**: K-POP、J-POP、J-ROCK、演劇等すべてのジャンル（拡張性100%実証済み）
- **🤖 AI信頼性フィルタリング**: Gemini APIによる自動品質判定・情報源評価
- **🌐 制限なし汎用検索**: Google Programmable Search Engine API（Web全体対象）
- **🗄️ Firestore完全連携**: アーティスト情報の保存・取得・永続化
- **🎨 Web UI**: アーティスト登録画面（artists.html）
- **📡 本番API**: スケジュール収集・アーティスト管理の完全API
- **🛠️ 日本語処理**: 完全な日本語対応（日付・時刻正規化含む）
- **🧪 テストシステム**: 汎用ジャンルテスト・検索エンジンテスト完備

### 📊 実証済み実績（2025-06-24テスト結果）
- **BLACKPINK (K-POP)**: 7件の高信頼度イベント（YG公式サイト等）
- **あいみょん (J-POP)**: 4件のライブ情報（公式サイト）
- **宝塚歌劇団 (演劇)**: 1件の公演情報（劇場公式サイト）
- **拡張性スコア**: 4/4ジャンル = 100%成功率

### 🔄 進行中 
- Google Calendar API自動追加機能の最適化
- 本番環境への最新システム反映

### ⏳ 将来拡張予定
- 追加ジャンル（クラシック、スポーツ、アニメイベント等）
- スケジュール自動通知システム
- CI/CD最適化（GitHub Actions）

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

### 📋 Universal Search System: 汎用システムへの進化（2025-06-24）

#### 🔄 重大なアーキテクチャ変更

| 変更項目 | 旧システム | 新システム | 実現効果 |
|----------|------------|------------|----------|
| **対象ジャンル** | K-POP専用 | 汎用エンターテイメント | ✅ 100%拡張性（実証済み） |
| **検索制限** | サイト制限あり | Web全体検索 | ✅ 情報源の大幅拡大 |
| **信頼性判定** | 手動サイト管理 | AI自動判定 | ✅ メンテナンス不要 |
| **ジャンル対応** | ハードコード | 動的パラメータ | ✅ 新ジャンル即座対応 |

#### 🎯 技術的革新

**Universal Schedule Prompt Template**:
- ジャンル変数 `{genre}` による動的対応
- 汎用信頼性基準（公式サイト・大手メディア・チケットサイト）
- 自動除外パターン（個人ブログ・噂・未確認情報）

**AI-Powered Quality Control**:
```python
async def collect_artist_schedules(self, artist_name: str, 
                                 days_ahead: int = 30, genre: str = "K-POP"):
    # 汎用検索 → AI信頼性判定 → 高品質情報抽出
    extracted_events = await self._extract_schedules_with_gemini(
        search_results, artist_name, genre
    )
```

#### 📊 実証済み成果（2025-06-24）

**拡張性テスト結果**:
- **K-POP**: BLACKPINK - 7件取得（信頼度: high/medium）
- **J-POP**: あいみょん - 4件取得（公式サイト情報）
- **演劇**: 宝塚歌劇団 - 1件取得（劇場公式）
- **拡張性スコア**: 4/4 = 100%

**品質評価**:
- 公式サイト情報の優先取得 ✅
- 個人ブログ・噂サイトの自動除外 ✅
- 日程情報の高精度抽出 ✅
- ジャンル適合性の自動判定 ✅

---

## 🛠️ 開発時の注意点（2025-06-24アップデート）

### 🔑 基本原則
1. **API キー管理**: 必ず環境変数で管理し、コミットしない
2. **日本語処理**: すべてのテキスト処理で`utils/japanese.py`を使用
3. **エラーハンドリング**: API失敗時の適切なフォールバック
4. **レート制限**: 外部API使用時は適切な遅延とリトライを実装

### 🎯 汎用システム開発指針
5. **ジャンル拡張性**: 新ジャンル追加時は`genre`パラメータを活用
6. **AI信頼性判定**: `UNIVERSAL_SCHEDULE_PROMPT_TEMPLATE`を使用
7. **品質管理**: `confidence >= 0.5` および `reliability != 'low'` を維持
8. **コスト監視**: Google Search API使用量の定期的な確認

### 🧪 テスト・検証
9. **汎用テスト**: 新機能は `scripts/test-universal-search.py` でジャンル横断テスト
10. **信頼性確認**: 取得情報の情報源と信頼度を必ず検証
11. **ログ出力**: 日本語でのログ出力を維持

### 📊 パフォーマンス監視
- 検索結果数とAPI使用量のバランス
- ジャンル別抽出精度の継続的測定
- 新ジャンル対応時の拡張性検証

## 🤖 Gemini AI プロンプト設計ガイドライン（2025-06-24）

### 🌟 汎用ジャンル対応プロンプト（推奨）

**UNIVERSAL_SCHEDULE_PROMPT_TEMPLATE**使用例:
```python
# あらゆるジャンルに対応
result = await collector.collect_artist_schedules(
    artist_name="あいみょん", 
    genre="J-POP"
)
result = await collector.collect_artist_schedules(
    artist_name="宝塚歌劇団", 
    genre="演劇"
)
```

### 🎯 旧K-POP専用プロンプト（後方互換性）

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
