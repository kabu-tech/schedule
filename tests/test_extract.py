# -*- coding: utf-8 -*-
"""
/extract エンドポイントのテスト
Gemini APIを使用したスケジュール情報抽出のテスト
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch, MagicMock

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


class TestExtractEndpoint:
    """POST /extract エンドポイントのテストクラス"""
    
    @patch('app.routers.extract.genai')
    def test_extract_success(self, mock_genai):
        """正常系：検索結果からスケジュール情報を抽出"""
        # Gemini APIのモック設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '''
        {
            "events": [
                {
                    "date": "2025-01-20",
                    "time": "18:00",
                    "title": "BLACKPINK WORLD TOUR 2025",
                    "artist": "BLACKPINK",
                    "type": "コンサート",
                    "location": "東京ドーム",
                    "source": "https://blackpink.com/tour2025",
                    "confidence": 0.95,
                    "reliability": "high"
                },
                {
                    "date": "2025-01-15",
                    "time": "",
                    "title": "Pink Venom 2",
                    "artist": "BLACKPINK",
                    "type": "リリース",
                    "location": "",
                    "source": "https://news.music.com/blackpink-new",
                    "confidence": 0.9,
                    "reliability": "high"
                }
            ]
        }
        '''
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        # リクエストデータ
        request_data = {
            "sources": [
                {
                    "title": "BLACKPINK WORLD TOUR 2025",
                    "url": "https://blackpink.com/tour2025",
                    "snippet": "BLACKPINKワールドツアー2025年1月20日東京ドーム開催決定"
                },
                {
                    "title": "BLACKPINK 新曲リリース",
                    "url": "https://news.music.com/blackpink-new",
                    "snippet": "BLACKPINK、1月15日に新シングル「Pink Venom 2」リリース"
                }
            ]
        }
        
        # APIリクエスト
        response = client.post("/extract", json=request_data)
        
        # アサーション
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        assert len(data["events"]) == 2
        
        # 最初のイベントの検証
        event = data["events"][0]
        assert event["date"] == "2025-01-20"
        assert event["type"] == "コンサート"
        assert event["confidence"] == 0.95
        assert event["reliability"] == "high"
    
    def test_extract_empty_sources(self):
        """異常系：sourcesが空の場合は400エラー"""
        response = client.post("/extract", json={"sources": []})
        assert response.status_code == 400
    
    def test_extract_invalid_format(self):
        """異常系：不正なフォーマットの場合は422エラー"""
        response = client.post("/extract", json={})
        assert response.status_code == 422
        
        response = client.post("/extract", json={"sources": "invalid"})
        assert response.status_code == 422
    
    @patch('app.routers.extract.genai')
    def test_extract_no_events_found(self, mock_genai):
        """正常系：スケジュール情報が見つからない場合"""
        # Gemini APIのモック設定
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"events": []}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        request_data = {
            "sources": [
                {
                    "title": "関係ない記事",
                    "url": "https://example.com",
                    "snippet": "スケジュールと関係ない内容"
                }
            ]
        }
        
        response = client.post("/extract", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []