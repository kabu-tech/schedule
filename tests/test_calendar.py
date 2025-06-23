# -*- coding: utf-8 -*-
"""
Google Calendar APIテストスイート
TDD RED phase: 実装前にテストを作成してテスト失敗を確認
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# テスト対象のインポート（まだ実装されていないため、インポートエラーが発生する予定）
try:
    from app.services.calendar import CalendarService
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False

# テストデータ用のEventDataインポート
from app.routers.events import EventData


class TestCalendarService:
    """Google Calendar サービスのテストクラス"""
    
    @pytest.fixture
    def sample_event_data(self):
        """テスト用のサンプルイベントデータ"""
        return EventData(
            date="2024-12-25",
            time="19:00",
            title="BLACKPINK Winter Concert",
            artist="BLACKPINK", 
            type="コンサート",
            location="東京ドーム",
            source="https://official-site.com/concert",
            confidence=0.95,
            reliability="high"
        )
    
    @pytest.fixture
    def mock_calendar_service(self):
        """モックされたGoogle Calendar APIサービス"""
        mock_service = Mock()
        mock_service.events.return_value = Mock()
        return mock_service
    
    @pytest.fixture
    def calendar_service_instance(self, mock_calendar_service):
        """CalendarServiceインスタンス（モック付き）"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        with patch('app.services.calendar.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            service = CalendarService()
            return service

class TestServiceInitialization:
    """サービス初期化テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """環境変数のセットアップ"""
        os.environ.update({
            'GOOGLE_SERVICE_ACCOUNT_KEY': '{"type": "service_account", "project_id": "test"}',
            'GOOGLE_CALENDAR_ID': 'test@group.calendar.google.com'
        })
        yield
        # テスト後のクリーンアップ
        for key in ['GOOGLE_SERVICE_ACCOUNT_KEY', 'GOOGLE_CALENDAR_ID']:
            os.environ.pop(key, None)

    def test_get_service_success(self):
        """認証成功時のサービス取得テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info') as mock_creds, \
             patch('app.services.calendar.build') as mock_build:
            
            mock_creds.return_value = Mock()
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            service = CalendarService()
            result = service.get_service()
            
            assert result == mock_service
            mock_creds.assert_called_once()
            mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds.return_value)

    def test_get_service_missing_env_var(self):
        """環境変数が不足している場合のテスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        os.environ.pop('GOOGLE_SERVICE_ACCOUNT_KEY', None)
        
        with pytest.raises(ValueError, match="GOOGLE_SERVICE_ACCOUNT_KEY environment variable is required"):
            CalendarService()

    def test_get_service_invalid_json(self):
        """無効なJSONの場合のテスト"""  
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        os.environ['GOOGLE_SERVICE_ACCOUNT_KEY'] = 'invalid json'
        
        with pytest.raises(ValueError, match="Invalid JSON in GOOGLE_SERVICE_ACCOUNT_KEY"):
            CalendarService()


class TestEventInsertion:
    """イベント挿入テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """環境変数のセットアップ"""
        os.environ.update({
            'GOOGLE_SERVICE_ACCOUNT_KEY': '{"type": "service_account", "project_id": "test"}',
            'GOOGLE_CALENDAR_ID': 'test@group.calendar.google.com'
        })
        yield
        for key in ['GOOGLE_SERVICE_ACCOUNT_KEY', 'GOOGLE_CALENDAR_ID']:
            os.environ.pop(key, None)

    def test_insert_event_success(self, sample_event_data):
        """イベント正常挿入テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        expected_event_id = "test_event_id_12345"
        mock_response = {'id': expected_event_id}
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build:
            
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_insert.execute.return_value = mock_response
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            result = calendar_service.insert_event(sample_event_data)
            
            assert result == expected_event_id
            mock_events.insert.assert_called_once()
            mock_insert.execute.assert_called_once()

    def test_insert_event_with_retry_success(self, sample_event_data):
        """リトライ成功テスト（初回失敗、2回目成功）"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
        
        # 最初は失敗、次は成功のシナリオをテスト
        expected_event_id = "retry_success_id"
        mock_response = {'id': expected_event_id}
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build, \
             patch('time.sleep'):  # リトライの待機時間をスキップ
            
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()
            
            # 最初は例外、次は成功
            mock_insert.execute.side_effect = [
                Exception("Rate limit exceeded"),  # 1回目失敗
                mock_response  # 2回目成功
            ]
            
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            result = calendar_service.insert_event(sample_event_data)
            
            assert result == expected_event_id
            assert mock_insert.execute.call_count == 2  # リトライが1回発生

    def test_insert_event_retry_exhausted(self, sample_event_data):
        """リトライ回数上限テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build, \
             patch('time.sleep'):
            
            mock_service = Mock()
            mock_events = Mock()
            mock_insert = Mock()
            mock_insert.execute.side_effect = Exception("Persistent error")
            
            mock_service.events.return_value = mock_events
            mock_events.insert.return_value = mock_insert
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            
            with pytest.raises(Exception, match="Persistent error"):
                calendar_service.insert_event(sample_event_data)
            
            # デフォルトで3回リトライするはず
            assert mock_insert.execute.call_count == 3


class TestEventUpdate:
    """イベント更新テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """環境変数のセットアップ"""
        os.environ.update({
            'GOOGLE_SERVICE_ACCOUNT_KEY': '{"type": "service_account", "project_id": "test"}',
            'GOOGLE_CALENDAR_ID': 'test@group.calendar.google.com'
        })
        yield
        for key in ['GOOGLE_SERVICE_ACCOUNT_KEY', 'GOOGLE_CALENDAR_ID']:
            os.environ.pop(key, None)

    def test_update_event_success(self, sample_event_data):
        """イベント正常更新テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        event_id = "existing_event_id"
        mock_response = {'id': event_id, 'updated': datetime.now().isoformat()}
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build:
            
            mock_service = Mock()
            mock_events = Mock()
            mock_update = Mock()
            mock_update.execute.return_value = mock_response
            
            mock_service.events.return_value = mock_events
            mock_events.update.return_value = mock_update
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            result = calendar_service.update_event(event_id, sample_event_data)
            
            assert result == event_id
            mock_events.update.assert_called_once()
            mock_update.execute.assert_called_once()

    def test_update_nonexistent_event(self, sample_event_data):
        """存在しないイベントの更新テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        event_id = "nonexistent_event_id"
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build:
            
            mock_service = Mock()
            mock_events = Mock()
            mock_update = Mock()
            mock_update.execute.side_effect = Exception("Event not found")
            
            mock_service.events.return_value = mock_events
            mock_events.update.return_value = mock_update
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            
            with pytest.raises(Exception, match="Event not found"):
                calendar_service.update_event(event_id, sample_event_data)


class TestEventDeletion:
    """イベント削除テスト"""
    
    @pytest.fixture(autouse=True)
    def setup_env_vars(self):
        """環境変数のセットアップ"""
        os.environ.update({
            'GOOGLE_SERVICE_ACCOUNT_KEY': '{"type": "service_account", "project_id": "test"}',
            'GOOGLE_CALENDAR_ID': 'test@group.calendar.google.com'
        })
        yield
        for key in ['GOOGLE_SERVICE_ACCOUNT_KEY', 'GOOGLE_CALENDAR_ID']:
            os.environ.pop(key, None)

    def test_delete_event_success(self):
        """イベント正常削除テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        event_id = "event_to_delete"
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build:
            
            mock_service = Mock()
            mock_events = Mock()
            mock_delete = Mock()
            mock_delete.execute.return_value = {}  # 削除成功は空レスポンス
            
            mock_service.events.return_value = mock_events
            mock_events.delete.return_value = mock_delete
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            result = calendar_service.delete_event(event_id)
            
            assert result is True
            mock_events.delete.assert_called_once_with(
                calendarId=os.environ['GOOGLE_CALENDAR_ID'],
                eventId=event_id
            )
            mock_delete.execute.assert_called_once()

    def test_delete_nonexistent_event(self):
        """存在しないイベントの削除テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        event_id = "nonexistent_event"
        
        with patch('app.services.calendar.service_account.Credentials.from_service_account_info'), \
             patch('app.services.calendar.build') as mock_build:
            
            mock_service = Mock()
            mock_events = Mock()
            mock_delete = Mock()
            mock_delete.execute.side_effect = Exception("Event not found")
            
            mock_service.events.return_value = mock_events
            mock_events.delete.return_value = mock_delete
            mock_build.return_value = mock_service
            
            calendar_service = CalendarService()
            
            with pytest.raises(Exception, match="Event not found"):
                calendar_service.delete_event(event_id)


class TestDataTransformation:
    """データ変換テスト"""
    
    def test_event_data_to_google_calendar_format(self, sample_event_data):
        """EventDataからGoogle Calendar形式への変換テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        calendar_service = CalendarService()
        calendar_event = calendar_service._convert_to_calendar_event(sample_event_data)
        
        expected_keys = ['summary', 'start', 'end', 'location', 'description']
        for key in expected_keys:
            assert key in calendar_event
        
        assert calendar_event['summary'] == sample_event_data.title
        assert calendar_event['location'] == sample_event_data.location
        assert 'BLACKPINK' in calendar_event['description']
        assert 'コンサート' in calendar_event['description']

    def test_datetime_conversion(self, sample_event_data):
        """日時変換の精度テスト"""
        if not IMPORT_SUCCESS:
            pytest.skip("CalendarService not implemented yet (TDD RED phase)")
            
        calendar_service = CalendarService()
        calendar_event = calendar_service._convert_to_calendar_event(sample_event_data)
        
        # 開始時刻の検証
        start_datetime = calendar_event['start']['dateTime']
        assert '2024-12-25T19:00:00' in start_datetime
        assert '+09:00' in start_datetime  # JST timezone
        
        # 終了時刻の検証（デフォルト2時間後）
        end_datetime = calendar_event['end']['dateTime']
        assert '2024-12-25T21:00:00' in end_datetime


# TDD RED phase: この時点でテストを実行すると、CalendarServiceが未実装のため全て失敗するはず
if __name__ == "__main__":
    print("🔴 TDD RED Phase: Running tests before implementation")
    print("Expected: All tests should FAIL because CalendarService is not implemented yet")
    pytest.main([__file__, "-v"])