# -*- coding: utf-8 -*-
"""
POST /events/save エンドポイントのテスト
Firestore保存機能のテスト
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch, MagicMock
import uuid

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


class TestEventsSaveEndpoint:
    """POST /events/save エンドポイントのテストクラス"""
    
    @patch('app.routers.events.uuid.uuid4')
    @patch('app.routers.events.firestore.Client')
    def test_events_save_success(self, mock_firestore_client, mock_uuid):
        """正常系：イベント保存成功 → 201 Created + IDを返す"""
        # UUIDのモック
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value=test_uuid)
        
        # Firestoreのモック設定
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.return_value = mock_client
        
        # リクエストデータ
        event_data = {
            "date": "2025-01-20",
            "time": "18:00",
            "title": "BLACKPINK WORLD TOUR 2025",
            "artist": "BLACKPINK",
            "type": "コンサート",
            "location": "東京ドーム",
            "source": "https://blackpink.com/tour2025",
            "confidence": 0.95,
            "reliability": "high"
        }
        
        # APIリクエスト
        response = client.post("/events/save", json=event_data)
        
        # アサーション
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "message" in data
        assert data["id"] == test_uuid
        assert "正常に保存されました" in data["message"]
        
        # Firestoreの呼び出し確認
        mock_client.collection.assert_called_with("events")
        mock_collection.document.assert_called_with(test_uuid)
    
    def test_events_save_invalid_format(self):
        """異常系：不正なJSONフォーマット → 422エラー"""
        # 必須フィールドが不足
        invalid_data = {
            "title": "イベント名のみ"
        }
        
        response = client.post("/events/save", json=invalid_data)
        assert response.status_code == 422
    
    def test_events_save_empty_data(self):
        """異常系：空のデータ → 422エラー"""
        response = client.post("/events/save", json={})
        assert response.status_code == 422
    
    def test_events_save_invalid_date_format(self):
        """異常系：不正な日付フォーマット → 422エラー"""
        invalid_data = {
            "date": "2025/01/20",  # 不正フォーマット
            "time": "18:00",
            "title": "BLACKPINK WORLD TOUR 2025",
            "artist": "BLACKPINK",
            "type": "コンサート",
            "location": "東京ドーム",
            "source": "https://blackpink.com/tour2025",
            "confidence": 0.95,
            "reliability": "high"
        }
        
        response = client.post("/events/save", json=invalid_data)
        assert response.status_code == 422
    
    @patch('app.routers.events.firestore.Client')
    def test_events_save_firestore_error(self, mock_firestore_client):
        """異常系：Firestoreエラー → 500エラー"""
        # Firestoreでエラーが発生する設定
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.set.side_effect = Exception("Firestore connection error")
        mock_collection.document.return_value = mock_doc_ref
        mock_client.collection.return_value = mock_collection
        mock_firestore_client.return_value = mock_client
        
        event_data = {
            "date": "2025-01-20",
            "time": "18:00",
            "title": "BLACKPINK WORLD TOUR 2025",
            "artist": "BLACKPINK",
            "type": "コンサート",
            "location": "東京ドーム",
            "source": "https://blackpink.com/tour2025",
            "confidence": 0.95,
            "reliability": "high"
        }
        
        response = client.post("/events/save", json=event_data)
        assert response.status_code == 500
    
    @patch('app.routers.events.firestore.Client')
    def test_events_save_uuid_generation(self, mock_firestore_client):
        """正常系：UUID形式のIDが生成される"""
        # Firestoreのモック設定
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_client.return_value = mock_client
        
        event_data = {
            "date": "2025-01-20",
            "time": "18:00",
            "title": "テストイベント",
            "artist": "テストアーティスト",
            "type": "コンサート",
            "location": "テスト会場",
            "source": "https://test.com",
            "confidence": 0.8,
            "reliability": "medium"
        }
        
        response = client.post("/events/save", json=event_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # UUIDフォーマットの検証
        returned_id = data["id"]
        # UUID形式の検証（ハイフンの位置確認）
        assert len(returned_id) == 36
        assert returned_id.count("-") == 4