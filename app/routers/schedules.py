# -*- coding: utf-8 -*-
"""
スケジュール収集APIルーター
本番用のスケジュール収集エンドポイント
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.services.schedule_collector import ScheduleCollector
from app.services.firestore_client import FirestoreClient
from app.services.register import ArtistRegisterService

logger = logging.getLogger(__name__)

# ルーターの作成
router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    responses={404: {"description": "Not found"}},
)

# リクエスト/レスポンスモデル
class ScheduleCollectionRequest(BaseModel):
    """スケジュール収集リクエスト"""
    artist_name: str = Field(..., min_length=1, max_length=100, description="アーティスト名")
    days_ahead: int = Field(30, ge=1, le=365, description="何日先まで検索するか")
    save_to_firestore: bool = Field(True, description="Firestoreに保存するか")
    auto_add_to_calendar: bool = Field(False, description="Google Calendarに自動追加するか")


class BatchCollectionRequest(BaseModel):
    """バッチ収集リクエスト"""
    artist_names: List[str] = Field(..., min_items=1, max_items=10, description="アーティスト名のリスト")
    days_ahead: int = Field(30, ge=1, le=365, description="何日先まで検索するか")
    save_to_firestore: bool = Field(True, description="Firestoreに保存するか")


class ScheduleCollectionResponse(BaseModel):
    """スケジュール収集レスポンス"""
    success: bool
    message: str
    artist_name: Optional[str] = None
    events_found: int = 0
    events: List[Dict[str, Any]] = []
    collection_id: Optional[str] = None
    collected_at: Optional[str] = None


class BatchCollectionResponse(BaseModel):
    """バッチ収集レスポンス"""
    success: bool
    message: str
    successful_collections: int = 0
    failed_collections: int = 0
    total_events: int = 0
    results: List[Dict[str, Any]] = []
    collection_id: Optional[str] = None
    collected_at: Optional[str] = None


# 依存関数
def get_schedule_collector() -> ScheduleCollector:
    """ScheduleCollectorのインスタンスを取得"""
    try:
        # 環境変数から設定を取得
        google_api_key = os.getenv('GOOGLE_API_KEY')
        google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not all([google_api_key, google_search_engine_id, gemini_api_key]):
            raise ValueError("必要な環境変数が設定されていません")
        
        # Firestoreクライアントの初期化
        try:
            firestore_client = FirestoreClient()
        except Exception as e:
            logger.warning(f"Firestore client initialization failed: {e}")
            firestore_client = None
        
        return ScheduleCollector(
            google_api_key=google_api_key,
            google_search_engine_id=google_search_engine_id,
            gemini_api_key=gemini_api_key,
            firestore_client=firestore_client
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize ScheduleCollector: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"スケジュール収集サービスの初期化に失敗しました: {str(e)}"
        )


def get_current_user_id() -> str:
    """現在のユーザーIDを取得（暫定実装）"""
    return "default_user"


# APIエンドポイント
@router.post("/collect", response_model=ScheduleCollectionResponse)
async def collect_artist_schedules(
    request: ScheduleCollectionRequest,
    background_tasks: BackgroundTasks,
    collector: ScheduleCollector = Depends(get_schedule_collector),
    user_id: str = Depends(get_current_user_id)
):
    """
    指定されたアーティストのスケジュール情報を収集
    """
    try:
        logger.info(f"Schedule collection request for: {request.artist_name}")
        
        # スケジュール収集を実行
        result = await collector.collect_artist_schedules(
            artist_name=request.artist_name,
            days_ahead=request.days_ahead
        )
        
        if not result['success']:
            return ScheduleCollectionResponse(
                success=False,
                message=result['message'],
                artist_name=request.artist_name
            )
        
        events = result.get('extracted_events', [])
        
        # Firestoreに保存（要求された場合）
        if request.save_to_firestore and events:
            background_tasks.add_task(
                _save_schedules_background,
                collector, events, request.artist_name
            )
        
        # Google Calendarに追加（要求された場合）
        if request.auto_add_to_calendar and events:
            background_tasks.add_task(
                _add_to_calendar_background,
                events, user_id
            )
        
        # コレクションIDの生成
        import hashlib
        collection_data = f"{request.artist_name}_{datetime.now().isoformat()}"
        collection_id = hashlib.md5(collection_data.encode()).hexdigest()[:12]
        
        return ScheduleCollectionResponse(
            success=True,
            message=result['message'],
            artist_name=request.artist_name,
            events_found=len(events),
            events=events,
            collection_id=collection_id,
            collected_at=result.get('collected_at')
        )
        
    except Exception as e:
        logger.error(f"Schedule collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"スケジュール収集中にエラーが発生しました: {str(e)}"
        )


@router.post("/collect-batch", response_model=BatchCollectionResponse)
async def collect_multiple_artists_schedules(
    request: BatchCollectionRequest,
    background_tasks: BackgroundTasks,
    collector: ScheduleCollector = Depends(get_schedule_collector),
    user_id: str = Depends(get_current_user_id)
):
    """
    複数アーティストのスケジュール情報を並行して収集
    """
    try:
        logger.info(f"Batch collection request for {len(request.artist_names)} artists")
        
        # バッチ収集を実行
        result = await collector.collect_multiple_artists_schedules(
            artist_names=request.artist_names,
            days_ahead=request.days_ahead
        )
        
        successful_collections = result.get('successful_collections', [])
        failed_collections = result.get('failed_collections', [])
        total_events = result.get('total_events', 0)
        
        # Firestoreに保存（要求された場合）
        if request.save_to_firestore and successful_collections:
            for collection_result in successful_collections:
                events = collection_result.get('extracted_events', [])
                artist_name = collection_result.get('artist_name', '')
                if events and artist_name:
                    background_tasks.add_task(
                        _save_schedules_background,
                        collector, events, artist_name
                    )
        
        # コレクションIDの生成
        import hashlib
        collection_data = f"batch_{datetime.now().isoformat()}"
        collection_id = hashlib.md5(collection_data.encode()).hexdigest()[:12]
        
        return BatchCollectionResponse(
            success=True,
            message=result['message'],
            successful_collections=len(successful_collections),
            failed_collections=len(failed_collections),
            total_events=total_events,
            results=successful_collections + failed_collections,
            collection_id=collection_id,
            collected_at=result.get('collected_at')
        )
        
    except Exception as e:
        logger.error(f"Batch collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"バッチ収集中にエラーが発生しました: {str(e)}"
        )


@router.post("/collect-registered")
async def collect_registered_artists_schedules(
    background_tasks: BackgroundTasks,
    days_ahead: int = 30,
    collector: ScheduleCollector = Depends(get_schedule_collector),
    user_id: str = Depends(get_current_user_id)
):
    """
    登録済みアーティストのスケジュール情報を自動収集
    """
    try:
        logger.info(f"Auto collection for registered artists, user: {user_id}")
        
        # Firestoreクライアントとアーティスト登録サービスの初期化
        try:
            firestore_client = FirestoreClient()
            artist_service = ArtistRegisterService(firestore_client=firestore_client)
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise HTTPException(
                status_code=500,
                detail="サービスの初期化に失敗しました"
            )
        
        # 登録済みアーティストを取得
        registered_artists = artist_service.get_user_artists(user_id)
        
        if not registered_artists:
            return {
                'success': False,
                'message': '登録されているアーティストがありません',
                'total_artists': 0,
                'total_events': 0
            }
        
        # 通知が有効なアーティストのみをフィルタ
        active_artists = [
            artist for artist in registered_artists 
            if artist.get('notification_enabled', True)
        ]
        
        if not active_artists:
            return {
                'success': False,
                'message': '通知が有効なアーティストがありません',
                'total_artists': len(registered_artists),
                'total_events': 0
            }
        
        # アーティスト名のリストを作成
        artist_names = [artist['name'] for artist in active_artists]
        
        # バッチ収集をバックグラウンドで実行
        background_tasks.add_task(
            _collect_registered_artists_background,
            collector, artist_names, days_ahead, user_id
        )
        
        return {
            'success': True,
            'message': f'{len(artist_names)}件のアーティストのスケジュール収集をバックグラウンドで開始しました',
            'total_artists': len(artist_names),
            'artists': artist_names,
            'started_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Auto collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"自動収集の開始に失敗しました: {str(e)}"
        )


@router.get("/status")
async def get_collection_status():
    """
    スケジュール収集システムの状態を取得
    """
    try:
        # 環境変数のチェック
        required_vars = [
            'GOOGLE_API_KEY',
            'GOOGLE_SEARCH_ENGINE_ID', 
            'GEMINI_API_KEY'
        ]
        
        env_status = {}
        for var in required_vars:
            env_status[var] = 'configured' if os.getenv(var) else 'missing'
        
        # Firestoreクライアントのチェック
        try:
            firestore_client = FirestoreClient()
            firestore_status = firestore_client.health_check()
        except Exception as e:
            firestore_status = {
                'status': 'error',
                'error': str(e)
            }
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'environment_variables': env_status,
            'firestore': firestore_status,
            'services': {
                'google_search': 'configured' if env_status.get('GOOGLE_API_KEY') == 'configured' else 'not_configured',
                'gemini_ai': 'configured' if env_status.get('GEMINI_API_KEY') == 'configured' else 'not_configured',
                'firestore': firestore_status.get('status', 'unknown')
            }
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


# バックグラウンドタスク
async def _save_schedules_background(collector: ScheduleCollector, 
                                   events: List[Dict[str, Any]], 
                                   artist_name: str):
    """Firestoreへの保存をバックグラウンドで実行"""
    try:
        logger.info(f"Background task: Saving {len(events)} events for {artist_name}")
        result = await collector.save_schedules_to_firestore(events, artist_name)
        logger.info(f"Background save completed: {result['message']}")
    except Exception as e:
        logger.error(f"Background save failed: {e}")


async def _add_to_calendar_background(events: List[Dict[str, Any]], user_id: str):
    """Google Calendarへの追加をバックグラウンドで実行"""
    try:
        logger.info(f"Background task: Adding {len(events)} events to calendar for user {user_id}")
        # TODO: Google Calendar連携の実装
        logger.info("Calendar integration not yet implemented")
    except Exception as e:
        logger.error(f"Background calendar add failed: {e}")


async def _collect_registered_artists_background(collector: ScheduleCollector,
                                                artist_names: List[str],
                                                days_ahead: int,
                                                user_id: str):
    """登録済みアーティストの収集をバックグラウンドで実行"""
    try:
        logger.info(f"Background task: Collecting schedules for {len(artist_names)} registered artists")
        
        result = await collector.collect_multiple_artists_schedules(
            artist_names=artist_names,
            days_ahead=days_ahead
        )
        
        # 成功した収集結果をFirestoreに保存
        for collection_result in result.get('successful_collections', []):
            events = collection_result.get('extracted_events', [])
            artist_name = collection_result.get('artist_name', '')
            if events and artist_name:
                await collector.save_schedules_to_firestore(events, artist_name)
        
        logger.info(f"Background collection completed: {result['message']}")
        
    except Exception as e:
        logger.error(f"Background collection failed: {e}")