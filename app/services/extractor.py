# -*- coding: utf-8 -*-
"""
スケジュール情報抽出モジュール
Vertex AI Gemini APIを使用してテキストからスケジュール情報を抽出
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from config import get_prompt, JAPANESE_PROMPTS
from utils.japanese import JapaneseTextProcessor

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleExtractor:
    """スケジュール情報抽出クラス"""
    
    def __init__(self, project_id: str, location: str = "asia-northeast1"):
        """
        初期化
        
        Args:
            project_id: Google Cloud プロジェクトID
            location: Vertex AIのリージョン
        """
        self.project_id = project_id
        self.location = location
        self.model_name = "gemini-1.5-pro"
        self.text_processor = JapaneseTextProcessor()
        
        # Vertex AI初期化
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(self.model_name)
        
        logger.info(f"Gemini API初期化完了 - プロジェクト: {project_id}, リージョン: {location}")
    
    def extract_schedules_from_text(self, text: str, artist_name: str = None) -> List[Dict[str, Any]]:
        """
        テキストからスケジュール情報を抽出
        
        Args:
            text: 抽出対象のテキスト
            artist_name: アーティスト名（オプション）
            
        Returns:
            抽出されたスケジュール情報のリスト
        """
        try:
            # テキストの前処理
            normalized_text = self.text_processor.normalize_text(text)
            
            # プロンプト生成
            prompt = self._create_extraction_prompt(normalized_text, artist_name)
            
            logger.info(f"Geminiでスケジュール抽出開始")
            
            # Gemini APIを呼び出し
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.warning("Geminiから空のレスポンス")
                return []
            
            # JSONレスポンスを解析
            schedules = self._parse_gemini_response(response.text)
            
            # 後処理
            processed_schedules = self._post_process_schedules(schedules, artist_name)
            
            logger.info(f"スケジュール{len(processed_schedules)}件を抽出")
            return processed_schedules
            
        except Exception as e:
            logger.error(f"スケジュール抽出エラー: {str(e)}")
            return []
    
    def _create_extraction_prompt(self, text: str, artist_name: str = None) -> str:
        """スケジュール抽出用のプロンプトを生成"""
        
        base_prompt = """
以下のテキストからK-POPスケジュール情報を抽出してください。

【抽出ルール】
1. 日付が明確に記載されているもののみ抽出
2. 過去の日付は除外
3. 時間が不明な場合は空文字を設定
4. 場所が不明な場合は空文字を設定
5. 確実でない情報は除外

【抽出対象】
- 日付（YYYY-MM-DD形式）
- 時間（HH:MM形式、不明の場合は空文字）
- イベント名
- アーティスト名
- イベント種別（コンサート、リリース、テレビ出演、ラジオ出演、イベント、その他）
- 場所（記載がある場合）

【テキスト】
{text}

【出力形式】
以下のJSON形式で回答してください：
```json
{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "アーティスト名",
            "type": "イベント種別",
            "location": "場所",
            "confidence": 0.9
        }}
    ]
}}
```
"""
        
        formatted_prompt = base_prompt.format(text=text)
        
        if artist_name:
            formatted_prompt += f"\n\n【アーティスト名】: {artist_name}"
            
        return formatted_prompt
    
    def _parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Geminiレスポンスを解析してスケジュール情報を抽出"""
        try:
            # JSONブロックを抽出
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # JSONブロックがない場合はレスポンス全体をJSONとして解析
                json_text = response_text
            
            # JSON解析
            data = json.loads(json_text)
            
            if 'events' in data:
                return data['events']
            else:
                logger.warning("レスポンスにeventsキーが見つかりません")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析エラー: {str(e)}")
            logger.debug(f"解析対象テキスト: {response_text}")
            return []
    
    def _post_process_schedules(self, schedules: List[Dict[str, Any]], 
                              artist_name: str = None) -> List[Dict[str, Any]]:
        """抽出されたスケジュール情報の後処理"""
        processed = []
        current_date = datetime.now().date()
        
        for schedule in schedules:
            try:
                # 必須項目チェック
                if not schedule.get('date') or not schedule.get('title'):
                    continue
                
                # 日付検証
                event_date = datetime.strptime(schedule['date'], '%Y-%m-%d').date()
                if event_date < current_date:
                    continue  # 過去の日付をスキップ
                
                # デフォルト値設定
                processed_schedule = {
                    'date': schedule['date'],
                    'time': schedule.get('time', ''),
                    'title': schedule.get('title', ''),
                    'artist': schedule.get('artist', artist_name or ''),
                    'type': schedule.get('type', 'その他'),
                    'location': schedule.get('location', ''),
                    'confidence': schedule.get('confidence', 0.8),
                    'source': 'gemini_extraction',
                    'extracted_at': datetime.now().isoformat()
                }
                
                # イベント種別の正規化
                processed_schedule['type'] = self._normalize_event_type(processed_schedule['type'])
                
                processed.append(processed_schedule)
                
            except ValueError as e:
                logger.warning(f"日付解析エラー: {schedule.get('date')} - {str(e)}")
                continue
        
        return processed
    
    def _normalize_event_type(self, event_type: str) -> str:
        """イベント種別を正規化"""
        type_mapping = {
            'concert': 'コンサート',
            'live': 'コンサート',
            'コンサート': 'コンサート',
            'ライブ': 'コンサート',
            'release': 'リリース',
            'リリース': 'リリース',
            '発売': 'リリース',
            'tv': 'テレビ出演',
            'テレビ': 'テレビ出演',
            'テレビ出演': 'テレビ出演',
            'radio': 'ラジオ出演',
            'ラジオ': 'ラジオ出演',
            'ラジオ出演': 'ラジオ出演',
            'event': 'イベント',
            'イベント': 'イベント',
            'fanmeeting': 'ファンミーティング',
            'ファンミーティング': 'ファンミーティング'
        }
        
        return type_mapping.get(event_type.lower(), 'その他')
    
    def extract_from_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ツイートデータからスケジュール情報を抽出
        
        Args:
            tweets: ツイートデータのリスト
            
        Returns:
            抽出されたスケジュール情報のリスト
        """
        all_schedules = []
        
        for tweet in tweets:
            content = tweet.get('content', '')
            username = tweet.get('username', '')
            display_name = tweet.get('display_name', '')
            
            if not content:
                continue
            
            # ツイート内容からスケジュール抽出
            schedules = self.extract_schedules_from_text(content, display_name)
            
            # ツイート情報を追加
            for schedule in schedules:
                schedule['source_tweet_id'] = tweet.get('id')
                schedule['source_tweet_url'] = tweet.get('url')
                schedule['source_username'] = username
                
            all_schedules.extend(schedules)
        
        return all_schedules
    
    def batch_extract_schedules(self, text_list: List[str], 
                               artist_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        複数のテキストから一括でスケジュール抽出
        
        Args:
            text_list: テキストのリスト
            artist_names: 対応するアーティスト名のリスト
            
        Returns:
            すべての抽出結果をまとめたリスト
        """
        all_schedules = []
        
        for i, text in enumerate(text_list):
            artist_name = artist_names[i] if artist_names and i < len(artist_names) else None
            schedules = self.extract_schedules_from_text(text, artist_name)
            all_schedules.extend(schedules)
        
        return all_schedules
    
    def validate_schedules(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        抽出されたスケジュール情報を検証
        
        Args:
            schedules: スケジュール情報のリスト
            
        Returns:
            検証済みのスケジュール情報
        """
        validated = []
        
        for schedule in schedules:
            # 必須項目チェック
            if not all([schedule.get('date'), schedule.get('title')]):
                continue
            
            # 日付形式チェック
            try:
                datetime.strptime(schedule['date'], '%Y-%m-%d')
            except ValueError:
                continue
            
            # 時間形式チェック（空文字の場合はOK）
            if schedule.get('time') and schedule['time']:
                try:
                    datetime.strptime(schedule['time'], '%H:%M')
                except ValueError:
                    schedule['time'] = ''  # 無効な時間形式は空文字に
            
            # 信頼度チェック
            confidence = schedule.get('confidence', 0.5)
            if confidence < 0.5:  # 信頼度が低い場合はスキップ
                continue
            
            validated.append(schedule)
        
        return validated

# 便利関数
def extract_schedules_from_tweets(tweets: List[Dict[str, Any]], 
                                project_id: str) -> List[Dict[str, Any]]:
    """
    ツイートからスケジュール情報を抽出する便利関数
    
    Args:
        tweets: ツイートデータのリスト
        project_id: Google Cloud プロジェクトID
        
    Returns:
        抽出されたスケジュール情報のリスト
    """
    extractor = ScheduleExtractor(project_id)
    return extractor.extract_from_tweets(tweets)

def extract_schedules_from_text(text: str, project_id: str, 
                               artist_name: str = None) -> List[Dict[str, Any]]:
    """
    テキストからスケジュール情報を抽出する便利関数
    
    Args:
        text: 抽出対象のテキスト
        project_id: Google Cloud プロジェクトID
        artist_name: アーティスト名
        
    Returns:
        抽出されたスケジュール情報のリスト
    """
    extractor = ScheduleExtractor(project_id)
    return extractor.extract_schedules_from_text(text, artist_name)

# 使用例
if __name__ == "__main__":
    # テスト用のコード
    test_text = """
    BTS WORLD TOUR 'SPEAK YOURSELF' THE FINAL
    2024年1月15日(月) 18:30開演
    東京ドーム
    
    新曲「Dynamite」2024年2月1日リリース決定！
    """
    
    project_id = "your-project-id"  # 実際のプロジェクトIDに変更
    
    try:
        schedules = extract_schedules_from_text(test_text, project_id, "BTS")
        print("抽出されたスケジュール:")
        for schedule in schedules:
            print(json.dumps(schedule, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"テスト実行エラー: {str(e)}")