# -*- coding: utf-8 -*-
"""
K-POP Schedule Auto-Feed メインエントリポイント
K-POPアーティストのスケジュール自動収集システム
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="K-POP Schedule Auto-Feed",
    description="K-POPアーティストのスケジュール自動収集システム",
    version="0.1.0"
)

# ルーターの登録
from app.routers import sources, extract, events
app.include_router(sources.router)
app.include_router(extract.router)
app.include_router(events.router)

# リクエスト/レスポンスモデル
class ScrapeRequest(BaseModel):
    """スクレイピングリクエスト"""
    query: str
    source: str = "twitter"  # twitter, web, all
    limit: int = 10

class ScheduleResponse(BaseModel):
    """スケジュールレスポンス"""
    success: bool
    message: str
    data: Optional[Dict] = None
    events: Optional[List[Dict]] = None

class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# ルートエンドポイント
@app.get("/", response_model=Dict[str, str])
async def root():
    """ルートエンドポイント"""
    return {
        "message": "K-POP Schedule Auto-Feed API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# ヘルスチェック
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """システムヘルスチェック"""
    jst = timezone(timedelta(hours=9))
    services_status = {
        "api": "healthy",
        "scraper": "not_implemented",
        "extractor": "not_implemented",
        "calendar": "not_implemented",
        "database": "not_connected"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(jst).isoformat(),
        version="0.1.0",
        services=services_status
    )

# テスト用エンドポイント
@app.post("/test/scrape", response_model=ScheduleResponse)
async def test_scrape(request: ScrapeRequest):
    """スクレイピングのテスト（モックデータ）"""
    try:
        logger.info(f"Test scrape request: {request.query}")
        
        # モックデータを返す
        mock_events = [
            {
                "date": "2024-01-20",
                "time": "18:00",
                "title": f"{request.query} - コンサート",
                "artist": request.query,
                "type": "コンサート",
                "location": "東京ドーム"
            },
            {
                "date": "2024-01-25",
                "time": "19:00",
                "title": f"{request.query} - ファンミーティング",
                "artist": request.query,
                "type": "ファンミーティング",
                "location": "横浜アリーナ"
            }
        ]
        
        return ScheduleResponse(
            success=True,
            message="テストデータを返しています",
            data={"source": request.source, "query": request.query, "mock_data": True},
            events=mock_events[:request.limit]
        )
            
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# エラーハンドラー
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTPエラーハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": {
                "status_code": exc.status_code,
                "detail": exc.detail
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """一般的なエラーハンドラー"""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "内部エラーが発生しました",
            "error": {
                "type": type(exc).__name__,
                "detail": str(exc)
            }
        }
    )

# 開発用：直接実行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",  # localhostに変更
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )