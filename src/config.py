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

def get_message(category: str, key: str) -> str:
    """日本語メッセージを取得"""
    return Config.MESSAGES.get(category, {}).get(key, f"{category}.{key}")

def get_prompt(prompt_name: str, **kwargs) -> str:
    """日本語プロンプトテンプレートを取得"""
    template = JAPANESE_PROMPTS.get(prompt_name, "")
    return template.format(**kwargs)