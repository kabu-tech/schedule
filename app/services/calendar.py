# -*- coding: utf-8 -*-
"""
Google Calendar API サービス
TDD GREEN phase: テストを満たす最小限の実装
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ロガー設定
logger = logging.getLogger(__name__)

# 型ヒント用インポート
from app.routers.events import EventData


class CalendarService:
    """Google Calendar APIサービスクラス"""
    
    def __init__(self):
        """
        CalendarServiceの初期化
        環境変数からサービスアカウント情報を取得し、認証を設定
        
        Raises:
            ValueError: 環境変数が不足している場合
            ValueError: JSONが無効な場合
        """
        # 環境変数の検証
        self.service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
        if not self.service_account_key:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY environment variable is required")
        
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
        if not self.calendar_id:
            raise ValueError("GOOGLE_CALENDAR_ID environment variable is required")
        
        # サービスアカウントキーのJSON検証
        try:
            self.service_account_info = json.loads(self.service_account_key)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY")
        
        # スコープ設定
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        
        # サービス初期化
        self._service = None
        
        logger.info("CalendarService initialized successfully")

    def get_service(self):
        """
        Google Calendar APIサービスを取得
        サービスアカウント認証を使用してGoogle Calendar APIクライアントを構築
        
        Returns:
            Google Calendar APIサービスオブジェクト
            
        Raises:
            Exception: 認証に失敗した場合
        """
        try:
            if self._service is None:
                # サービスアカウント認証情報の作成
                credentials = service_account.Credentials.from_service_account_info(
                    self.service_account_info, 
                    scopes=self.scopes
                )
                
                # Google Calendar APIサービスの構築
                self._service = build('calendar', 'v3', credentials=credentials)
                
                logger.info("Google Calendar service authenticated successfully")
            
            return self._service
            
        except Exception as e:
            logger.error(f"Failed to authenticate Google Calendar service: {e}")
            raise

    def insert_event(self, event_data: EventData, max_retries: int = 3) -> str:
        """
        カレンダーにイベントを挿入
        指数バックオフによるリトライ機能付き
        
        Args:
            event_data: 挿入するイベントデータ
            max_retries: 最大リトライ回数
            
        Returns:
            作成されたイベントのID
            
        Raises:
            Exception: 最大リトライ回数に達した場合、または致命的なエラーの場合
        """
        service = self.get_service()
        calendar_event = self._convert_to_calendar_event(event_data)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Inserting event: {event_data.title} (attempt {attempt + 1}/{max_retries})")
                
                result = service.events().insert(
                    calendarId=self.calendar_id,
                    body=calendar_event
                ).execute()
                
                event_id = result['id']
                logger.info(f"Event inserted successfully with ID: {event_id}")
                return event_id
                
            except HttpError as e:
                if e.resp.status in [429, 500, 502, 503, 504]:  # リトライ可能なエラー
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1  # 指数バックオフ
                        logger.warning(f"Retryable error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for event insertion: {e}")
                        raise
                else:
                    # リトライ不可能なエラー
                    logger.error(f"Non-retryable error during event insertion: {e}")
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Generic error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded for event insertion: {e}")
                    raise

    def update_event(self, event_id: str, event_data: EventData, max_retries: int = 3) -> str:
        """
        既存のカレンダーイベントを更新
        指数バックオフによるリトライ機能付き
        
        Args:
            event_id: 更新するイベントのID
            event_data: 更新後のイベントデータ
            max_retries: 最大リトライ回数
            
        Returns:
            更新されたイベントのID
            
        Raises:
            Exception: 最大リトライ回数に達した場合、またはイベントが見つからない場合
        """
        service = self.get_service()
        calendar_event = self._convert_to_calendar_event(event_data)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Updating event: {event_id} (attempt {attempt + 1}/{max_retries})")
                
                result = service.events().update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=calendar_event
                ).execute()
                
                updated_event_id = result['id']
                logger.info(f"Event updated successfully: {updated_event_id}")
                return updated_event_id
                
            except HttpError as e:
                if e.resp.status == 404:
                    logger.error(f"Event not found: {event_id}")
                    raise Exception("Event not found")
                elif e.resp.status in [429, 500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1
                        logger.warning(f"Retryable error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for event update: {e}")
                        raise
                else:
                    logger.error(f"Non-retryable error during event update: {e}")
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Generic error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded for event update: {e}")
                    raise

    def delete_event(self, event_id: str, max_retries: int = 3) -> bool:
        """
        カレンダーからイベントを削除
        指数バックオフによるリトライ機能付き
        
        Args:
            event_id: 削除するイベントのID
            max_retries: 最大リトライ回数
            
        Returns:
            削除が成功した場合True
            
        Raises:
            Exception: 最大リトライ回数に達した場合、またはイベントが見つからない場合  
        """
        service = self.get_service()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Deleting event: {event_id} (attempt {attempt + 1}/{max_retries})")
                
                service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()
                
                logger.info(f"Event deleted successfully: {event_id}")
                return True
                
            except HttpError as e:
                if e.resp.status == 404:
                    logger.error(f"Event not found for deletion: {event_id}")
                    raise Exception("Event not found")
                elif e.resp.status in [429, 500, 502, 503, 504]:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + 1
                        logger.warning(f"Retryable error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for event deletion: {e}")
                        raise
                else:
                    logger.error(f"Non-retryable error during event deletion: {e}")
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Generic error occurred (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded for event deletion: {e}")
                    raise

    def _convert_to_calendar_event(self, event_data: EventData) -> Dict[str, Any]:
        """
        EventDataオブジェクトをGoogle Calendar API形式に変換
        
        Args:
            event_data: 変換するイベントデータ
            
        Returns:
            Google Calendar API形式のイベント辞書
        """
        # 日時の処理（JST/Asia/Tokyoタイムゾーン）
        event_datetime = f"{event_data.date}T{event_data.time}:00+09:00"
        
        # 終了時間の計算（デフォルト2時間後）
        start_dt = datetime.fromisoformat(event_datetime.replace('+09:00', ''))
        end_dt = start_dt + timedelta(hours=2)
        end_datetime = f"{end_dt.strftime('%Y-%m-%dT%H:%M:%S')}+09:00"
        
        # 説明文の構築
        description_parts = [
            f"アーティスト: {event_data.artist}",
            f"イベント種別: {event_data.type}",
            f"信頼度: {event_data.confidence:.2f}",
            f"信頼性: {event_data.reliability}",
            f"情報源: {event_data.source}"
        ]
        description = "\n".join(description_parts)
        
        # Google Calendar API形式のイベント
        calendar_event = {
            'summary': event_data.title,
            'location': event_data.location,
            'description': description,
            'start': {
                'dateTime': event_datetime,
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Tokyo',
            },
            # カスタムプロパティ（追跡用）
            'extendedProperties': {
                'private': {
                    'artist': event_data.artist,
                    'event_type': event_data.type,
                    'confidence': str(event_data.confidence),
                    'reliability': event_data.reliability,
                    'source': event_data.source
                }
            },
            # リマインダー設定
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1日前
                    {'method': 'popup', 'minutes': 60},       # 1時間前
                ],
            },
        }
        
        logger.debug(f"Converted EventData to Calendar event: {event_data.title}")
        return calendar_event

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        指定されたIDのイベントを取得
        
        Args:
            event_id: 取得するイベントのID
            
        Returns:
            イベントデータ（見つからない場合はNone）
            
        Raises:
            Exception: API呼び出しに失敗した場合
        """
        try:
            service = self.get_service()
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Event retrieved successfully: {event_id}")
            return event
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event not found: {event_id}")
                return None
            else:
                logger.error(f"Error retrieving event {event_id}: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving event {event_id}: {e}")
            raise

    def list_events(self, time_min: Optional[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        カレンダーからイベント一覧を取得
        
        Args:
            time_min: 取得開始時刻（ISO形式、デフォルトは現在時刻）
            max_results: 最大取得件数
            
        Returns:
            イベントのリスト
            
        Raises:
            Exception: API呼び出しに失敗した場合
        """
        try:
            service = self.get_service()
            
            if time_min is None:
                time_min = datetime.now().isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} events from calendar")
            return events
            
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            raise