# -*- coding: utf-8 -*-
"""
Google Programmable Search Engine APIを使用した情報源検索エンドポイント
"""

import os
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sources", response_model=List[Dict[str, str]])
async def search_sources(q: str = Query(..., description="検索クエリ文字列")) -> List[Dict[str, str]]:
    """
    Google Search APIで検索し、最初の3件を返す
    
    Args:
        q: 検索クエリ文字列
        
    Returns:
        検索結果のリスト（最大3件）
        各要素: {title, url, snippet}
    """
    # クエリパラメータのバリデーション
    if not q or q.strip() == "":
        raise HTTPException(status_code=400, detail="クエリパラメータ 'q' が空です")
    
    # 環境変数から認証情報を取得
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if not api_key or not search_engine_id:
        logger.error("Google API credentials not found in environment variables")
        raise HTTPException(status_code=500, detail="API設定エラー")
    
    try:
        # Google Search APIクライアントを構築
        service = build("customsearch", "v1", developerKey=api_key)
        
        # 検索を実行（最大3件）
        result = service.cse().list(
            q=q,
            cx=search_engine_id,
            num=3,
            lr="lang_ja"  # 日本語優先
        ).execute()
        
        # レスポンス形式に変換
        items = result.get("items", [])
        response_data = []
        
        for item in items[:3]:  # 最大3件
            response_data.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return response_data
        
    except HttpError as e:
        logger.error(f"Google Search API error: {e}")
        raise HTTPException(status_code=500, detail="検索APIエラー")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="内部エラー")