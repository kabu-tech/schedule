# -*- coding: utf-8 -*-
"""
K-POP Schedule Auto-Feed 設定ファイル
日本語プロンプトとメッセージの設定
"""

import os
import locale

# 日本語ロケール設定
try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Japanese_Japan.932')
    except locale.Error:
        pass  # デフォルトロケールを使用

# アプリケーション設定
class Config:
    """アプリケーション設定クラス"""
    
    # 基本設定
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TIMEZONE = 'Asia/Tokyo'
    LANGUAGE = 'ja'
    ENCODING = 'utf-8'
    
    # 日本語メッセージ
    MESSAGES = {
        'success': {
            'schedule_added': 'スケジュールが正常に追加されました',
            'data_saved': 'データが保存されました',
            'calendar_updated': 'カレンダーが更新されました'
        },
        'error': {
            'invalid_input': '入力内容に問題があります',
            'api_error': 'API接続でエラーが発生しました',
            'parse_error': 'データの解析に失敗しました'
        },
        'info': {
            'processing': '処理中...',
            'extracting': 'スケジュール情報を抽出中...',
            'uploading': 'カレンダーにアップロード中...'
        }
    }

# 日本語プロンプトテンプレート
JAPANESE_PROMPTS = {
    'schedule_extraction': """
以下のテキストからK-POPスケジュール情報を抽出してください。

抽出対象：
- 日付（YYYY-MM-DD形式）
- 時間（HH:MM形式、不明の場合は空欄）
- イベント名
- アーティスト名
- イベント種別（コンサート、リリース、テレビ出演など）
- 場所（記載がある場合）

テキスト：
{text}

JSON形式で回答してください：
```json
{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "アーティスト名",
            "type": "イベント種別",
            "location": "場所"
        }}
    ]
}}
```
""",

    'data_validation': """
以下のスケジュールデータの妥当性を確認してください：

データ：
{data}

確認項目：
1. 日付形式が正しいか
2. 必須項目が入力されているか
3. 重複するイベントがないか

問題がある場合は修正案を提示してください。
""",

    'calendar_description': """
{artist}の{event_type}「{title}」

📅 日時: {date} {time}
📍 場所: {location}
🎵 アーティスト: {artist}

※このイベントは自動収集システムにより追加されました
"""
}

# 汎用ジャンル対応 改良版Gemini信頼性フィルタリングプロンプト
UNIVERSAL_SCHEDULE_PROMPT_TEMPLATE = """
以下の検索結果から、{artist_name}の信頼性の高い{genre}スケジュール情報のみを抽出してください。

【汎用信頼性判定基準】
高信頼度：
- 公式サイト（アーティスト・レーベル・事務所の公式サイト）
- 大手メディア（新聞社、テレビ局、音楽専門メディア）
- 公式チケットサイト（e+、チケットぴあ、ローソンチケット、イープラスなど）
- 政府・自治体の公式発表
- 認証済み公式SNSアカウント
- 確立された音楽・エンターテイメント情報サイト

低信頼度（無視する）：
- 個人ブログ・まとめサイト・アフィリエイトサイト
- 「〜かも」「〜らしい」「噂」「予想」「リーク」「憶測」を含む投稿
- 匿名掲示板・SNSの非公式投稿
- 「未確認」「情報待ち」「ファンの予想」を含む情報
- Wikiサイト・フォーラム・Q&Aサイト

【抽出ルール】
1. 明確な日付が記載されているもののみ
2. 過去の日付は除外
3. 信頼度0.7未満の情報は除外
4. 重複する情報は信頼度の高いものを優先
5. {artist_name}に関連しないイベントは除外
6. {genre}ジャンルに適合しない情報は除外

【検索結果】
{search_results}

【出力形式】
以下のJSON形式でのみ回答してください。他の文章は含めないでください。

{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "{artist_name}",
            "type": "コンサート|リリース|テレビ出演|ラジオ出演|イベント|ファンミーティング|その他",
            "location": "開催場所",
            "source": "https://...",
            "confidence": 0.9,
            "reliability": "high|medium|low",
            "genre": "{genre}"
        }}
    ]
}}

信頼性が低い場合や該当する情報がない場合は、空の配列を返してください：
{{
    "events": []
}}
"""

# K-POP専用（後方互換性のため残す）
JAPANESE_SCHEDULE_PROMPT_TEMPLATE = """
以下の検索結果から、{artist_name}の信頼性の高いK-POPスケジュール情報のみを抽出してください。

【信頼性判定基準】
高信頼度：
- 公式サイト（.com、.jp、.kr等で「official」「artist名」を含むドメイン）
- 大手メディア（NHK、朝日新聞、音楽ナタリー、Billboard JAPANなど）
- 公式チケットサイト（e+、チケットぴあ、ローソンチケット、イープラスなど）
- 行政機関の発表
- 公式SNSアカウント（認証済み）

低信頼度（無視する）：
- 個人ブログ・まとめサイト
- 「〜かも」「〜らしい」「噂」「予想」「リーク」を含む投稿
- 匿名掲示板・SNSの非公式投稿
- 「未確認」「情報待ち」を含む情報
- ファンサイトの推測・予想記事

【抽出ルール】
1. 明確な日付が記載されているもののみ
2. 過去の日付は除外
3. 信頼度0.7未満の情報は除外
4. 重複する情報は信頼度の高いものを優先
5. {artist_name}に関連しないイベントは除外

【検索結果】
{search_results}

【出力形式】
以下のJSON形式でのみ回答してください。他の文章は含めないでください。

{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "{artist_name}",
            "type": "コンサート|リリース|テレビ出演|ラジオ出演|イベント|ファンミーティング|その他",
            "location": "開催場所",
            "source": "https://...",
            "confidence": 0.9,
            "reliability": "high|medium|low"
        }}
    ]
}}

信頼性が低い場合や該当する情報がない場合は、空の配列を返してください：
{{
    "events": []
}}
"""

def get_message(category: str, key: str) -> str:
    """日本語メッセージを取得"""
    return Config.MESSAGES.get(category, {}).get(key, f"{category}.{key}")

def get_prompt(prompt_name: str, **kwargs) -> str:
    """日本語プロンプトテンプレートを取得"""
    template = JAPANESE_PROMPTS.get(prompt_name, "")
    return template.format(**kwargs)