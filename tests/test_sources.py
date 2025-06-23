# -*- coding: utf-8 -*-
"""
/sources エンドポイントのテスト
Google Programmable Search Engine APIをモックしてテスト
"""

import pytest
import responses
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import patch

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


class TestSourcesEndpoint:
    """GET /sources エンドポイントのテストクラス"""
    
    @patch('app.routers.sources.build')
    def test_sources_success(self, mock_build):
        """正常系：q=Blackpinkで3件以下の結果を返す"""
        # Google Search APIのモックレスポンス
        mock_response = {
            "items": [
                {
                    "title": "BLACKPINK WORLD TOUR 2025",
                    "link": "https://blackpink.com/tour2025",
                    "snippet": "BLACKPINKワールドツアー2025年1月20日東京ドーム開催決定"
                },
                {
                    "title": "BLACKPINK 新曲リリース",
                    "link": "https://news.music.com/blackpink-new",
                    "snippet": "BLACKPINK、1月15日に新シングル「Pink Venom 2」リリース"
                },
                {
                    "title": "BLACKPINK TV出演情報",
                    "link": "https://tv.example.com/blackpink",
                    "snippet": "1月18日放送のミュージックステーションにBLACKPINK出演"
                }
            ]
        }
        
        # モックサービスの設定
        mock_service = mock_build.return_value
        mock_cse = mock_service.cse.return_value
        mock_cse.list.return_value.execute.return_value = mock_response
        
        # APIリクエスト
        response = client.get("/sources?q=Blackpink")
        
        # アサーション
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 3
        assert all(key in data[0] for key in ["title", "url", "snippet"])
    
    def test_sources_empty_query(self):
        """異常系：qパラメータが空の場合は400エラー"""
        response = client.get("/sources?q=")
        assert response.status_code == 400
        
        # qパラメータが存在しない場合は422（FastAPIのバリデーションエラー）
        response = client.get("/sources")
        assert response.status_code == 422
    
    @patch('app.routers.sources.build')
    def test_sources_response_format(self, mock_build):
        """レスポンス形式の検証：{title, url, snippet}"""
        # Google Search APIのモックレスポンス
        mock_response = {
            "items": [
                {
                    "title": "Test Title",
                    "link": "https://example.com",
                    "snippet": "Test snippet"
                }
            ]
        }
        
        # モックサービスの設定
        mock_service = mock_build.return_value
        mock_cse = mock_service.cse.return_value
        mock_cse.list.return_value.execute.return_value = mock_response
        
        response = client.get("/sources?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        # 各項目の形式を検証
        item = data[0]
        assert "title" in item
        assert "url" in item
        assert "snippet" in item
        assert isinstance(item["title"], str)
        assert isinstance(item["url"], str)
        assert isinstance(item["snippet"], str)