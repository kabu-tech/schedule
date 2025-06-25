# -*- coding: utf-8 -*-
"""
Universal Entertainment Schedule Auto-Feed メインエントリポイント
あらゆるジャンルのアーティスト・エンターテイメント情報を自動収集するシステム
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# カレンダー機能のインポート
from app.services.calendar import CalendarService
from app.routers.events import EventData

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Universal Entertainment Schedule Auto-Feed",
    description="あらゆるジャンルのアーティスト・エンターテイメント情報を自動収集するシステム",
    version="0.1.0"
)

# ルーターの登録
from app.routers import sources, extract, events, artists, schedules
app.include_router(sources.router)
app.include_router(extract.router)
app.include_router(events.router)
app.include_router(artists.router)
app.include_router(schedules.router)

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

class CalendarInsertResponse(BaseModel):
    """カレンダー挿入レスポンス"""
    success: bool
    message: str
    event_id: Optional[str] = None
    calendar_url: Optional[str] = None

class CalendarEventResponse(BaseModel):
    """カレンダーイベント取得レスポンス"""
    success: bool
    message: str
    event: Optional[Dict] = None

# ルートエンドポイント
@app.get("/", response_model=Dict[str, str])
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Universal Entertainment Schedule Auto-Feed API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# ヘルスチェック
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """システムヘルスチェック"""
    jst = timezone(timedelta(hours=9))
    # 実際の実装状況をチェック
    services_status = {
        "api": "healthy",
        "google_search": "implemented",  # Google Search API実装済み
        "gemini_extractor": "implemented",  # Gemini抽出機能実装済み
        "calendar": "implemented",  # Google Calendar連携実装済み
        "firestore": "implemented",  # Firestore連携実装済み
        "schedule_collector": "implemented",  # スケジュール収集サービス実装済み
        "artist_registration": "implemented"  # アーティスト登録機能実装済み
    }
    
    # Firestore接続状況を確認
    try:
        from app.services.firestore_client import FirestoreClient
        firestore_client = FirestoreClient()
        firestore_health = firestore_client.health_check()
        if firestore_health.get('status') == 'healthy':
            services_status['firestore'] = 'healthy'
        else:
            services_status['firestore'] = 'unhealthy'
    except Exception as e:
        services_status['firestore'] = f'error: {str(e)}'
    
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

# Google Calendar連携エンドポイント
@app.post("/events/insert", response_model=CalendarInsertResponse)
async def insert_calendar_event(event: EventData):
    """
    イベントをGoogle Calendarに挿入
    
    Args:
        event: 挿入するイベントデータ
        
    Returns:
        挿入結果（成功/失敗、イベントID、カレンダーURL）
    """
    try:
        logger.info(f"Calendar insert request for event: {event.title}")
        
        # CalendarServiceのインスタンス化
        calendar_service = CalendarService()
        
        # イベントをカレンダーに挿入
        event_id = calendar_service.insert_event(event)
        
        # カレンダーURLの構築（Googleカレンダーでイベントを表示）
        calendar_url = f"https://calendar.google.com/calendar/event?eid={event_id}"
        
        logger.info(f"Event inserted successfully: {event_id}")
        
        return CalendarInsertResponse(
            success=True,
            message=f"イベント '{event.title}' がカレンダーに正常に追加されました",
            event_id=event_id,
            calendar_url=calendar_url
        )
        
    except ValueError as e:
        # 設定エラー（環境変数不足など）
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"設定エラー: {str(e)}"
        )
        
    except Exception as e:
        # その他のエラー
        logger.error(f"Calendar insert error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"カレンダー挿入エラー: {str(e)}"
        )

@app.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(event_id: str):
    """
    指定されたIDのカレンダーイベントを取得
    
    Args:
        event_id: 取得するイベントのID
        
    Returns:
        イベント情報
    """
    try:
        logger.info(f"Calendar get request for event: {event_id}")
        
        calendar_service = CalendarService()
        event = calendar_service.get_event(event_id)
        
        if event is None:
            return CalendarEventResponse(
                success=False,
                message=f"イベント '{event_id}' が見つかりませんでした",
                event=None
            )
        
        return CalendarEventResponse(
            success=True,
            message="イベントを正常に取得しました",
            event=event
        )
        
    except Exception as e:
        logger.error(f"Calendar get error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"カレンダー取得エラー: {str(e)}"
        )

@app.delete("/events/{event_id}")
async def delete_calendar_event(event_id: str):
    """
    指定されたIDのカレンダーイベントを削除
    
    Args:
        event_id: 削除するイベントのID
        
    Returns:
        削除結果
    """
    try:
        logger.info(f"Calendar delete request for event: {event_id}")
        
        calendar_service = CalendarService()
        success = calendar_service.delete_event(event_id)
        
        if success:
            return {"success": True, "message": f"イベント '{event_id}' を正常に削除しました"}
        else:
            return {"success": False, "message": f"イベント '{event_id}' の削除に失敗しました"}
        
    except Exception as e:
        logger.error(f"Calendar delete error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"カレンダー削除エラー: {str(e)}"
        )

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