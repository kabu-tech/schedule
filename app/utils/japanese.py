# -*- coding: utf-8 -*-
"""
日本語処理ユーティリティ
"""

import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any

class JapaneseTextProcessor:
    """日本語テキスト処理クラス"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """テキストの正規化（全角・半角統一）"""
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    @staticmethod
    def extract_date_jp(text: str) -> Optional[str]:
        """日本語テキストから日付を抽出"""
        patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年1月15日
            r'(\d{1,2})/(\d{1,2})',  # 1/15
            r'(\d{1,2})月(\d{1,2})日',  # 1月15日
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 3:  # 年月日
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif len(match.groups()) == 2:  # 月日のみ
                    month, day = match.groups()
                    current_year = datetime.now().year
                    return f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None
    
    @staticmethod
    def extract_time_jp(text: str) -> Optional[str]:
        """日本語テキストから時刻を抽出"""
        patterns = [
            r'(\d{1,2}):(\d{2})',  # 19:30
            r'(\d{1,2})時(\d{1,2})?分?',  # 19時30分 or 19時
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2 and match.group(2):
                    hour, minute = match.groups()
                    return f"{hour.zfill(2)}:{minute.zfill(2)}"
                elif len(match.groups()) >= 1:
                    hour = match.group(1)
                    return f"{hour.zfill(2)}:00"
        
        return None
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """日付文字列を標準形式(YYYY-MM-DD)に正規化"""
        if not date_str:
            return None
        
        # 既に標準形式の場合
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # 日本語日付から抽出
        extracted = JapaneseTextProcessor.extract_date_jp(date_str)
        if extracted:
            return extracted
        
        # その他の形式を試行
        try:
            # ISO形式のパース試行
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            # スラッシュ区切り (YYYY/MM/DD)
            if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_str):
                parts = date_str.split('/')
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def normalize_time(time_str: str) -> Optional[str]:
        """時刻文字列を標準形式(HH:MM)に正規化"""
        if not time_str:
            return None
        
        # 既に標準形式の場合
        if re.match(r'^\d{2}:\d{2}$', time_str):
            return time_str
        
        # 日本語時刻から抽出
        extracted = JapaneseTextProcessor.extract_time_jp(time_str)
        if extracted:
            return extracted
        
        # その他の形式を試行
        try:
            # 単純な時:分形式
            if re.match(r'^\d{1,2}:\d{2}$', time_str):
                parts = time_str.split(':')
                return f"{parts[0].zfill(2)}:{parts[1]}"
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def detect_event_type(text: str) -> str:
        """テキストからイベント種別を判定"""
        event_types = {
            'コンサート': ['コンサート', 'ライブ', 'LIVE', 'CONCERT'],
            'リリース': ['リリース', '発売', 'RELEASE', 'MV', 'アルバム', 'シングル'],
            'テレビ出演': ['テレビ', 'TV', '出演', '放送'],
            'ラジオ出演': ['ラジオ', 'RADIO'],
            'イベント': ['イベント', 'EVENT', 'ファンミーティング'],
            'その他': []
        }
        
        text_upper = text.upper()
        for event_type, keywords in event_types.items():
            for keyword in keywords:
                if keyword.upper() in text_upper:
                    return event_type
        
        return 'その他'

def format_japanese_datetime(dt: datetime) -> str:
    """日本語形式の日時文字列を生成"""
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[dt.weekday()]
    
    return f"{dt.year}年{dt.month}月{dt.day}日（{weekday}） {dt.strftime('%H:%M')}"

def validate_japanese_input(data: Dict[str, Any]) -> Dict[str, str]:
    """日本語入力データの検証"""
    errors = {}
    
    # 必須項目チェック
    required_fields = {
        'title': 'イベント名',
        'artist': 'アーティスト名',
        'date': '日付'
    }
    
    for field, name in required_fields.items():
        if not data.get(field):
            errors[field] = f"{name}を入力してください"
    
    # 日付形式チェック
    if data.get('date'):
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            errors['date'] = '日付の形式が正しくありません（YYYY-MM-DD）'
    
    return errors