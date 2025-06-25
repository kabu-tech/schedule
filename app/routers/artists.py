# -*- coding: utf-8 -*-
"""
アーティスト登録APIルーター
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.services.register import ArtistRegisterService
from app.services.firestore_client import FirestoreClient
from app.services.schedule_collector import ScheduleCollector

logger = logging.getLogger(__name__)

# ルーターの作成
router = APIRouter(
    prefix="/artists",
    tags=["artists"],
    responses={404: {"description": "Not found"}},
)

# テンプレートの設定
import os
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=template_dir)

# Firestoreクライアントの初期化（エラーハンドリング付き）
try:
    firestore_client = FirestoreClient()
    logger.info("FirestoreClient initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FirestoreClient: {e}")
    logger.warning("Using ArtistRegisterService with memory-only backend")
    firestore_client = None

# サービスのインスタンス（Firestoreクライアント付き）
artist_service = ArtistRegisterService(firestore_client=firestore_client)


# リクエスト/レスポンスモデル
class ArtistRegisterRequest(BaseModel):
    """アーティスト登録リクエスト"""
    artist_name: str = Field(..., min_length=1, max_length=100, description="アーティスト名")
    notification_enabled: bool = Field(True, description="通知を有効にするか")


class ArtistUpdateRequest(BaseModel):
    """アーティスト更新リクエスト"""
    notification_enabled: bool = Field(..., description="通知を有効にするか")


class ArtistResponse(BaseModel):
    """アーティスト情報レスポンス"""
    id: str
    name: str
    original_name: str
    notification_enabled: bool
    registered_at: str
    last_updated: str


class ArtistListResponse(BaseModel):
    """アーティスト一覧レスポンス"""
    artists: List[ArtistResponse]
    total: int


class SearchResponse(BaseModel):
    """検索結果レスポンス"""
    suggestions: List[str]


# 仮のユーザーID（認証実装までの暫定）
def get_current_user_id() -> str:
    """現在のユーザーIDを取得（暫定実装）"""
    return "default_user"


# Web UIエンドポイント
@router.get("/", response_class=HTMLResponse)
async def artists_page(request: Request):
    """
    アーティスト登録ページを表示
    """
    user_id = get_current_user_id()
    artists = artist_service.get_user_artists(user_id)
    
    return templates.TemplateResponse(
        "artists.html",
        {
            "request": request,
            "artists": artists,
            "suggested_artists": artist_service.SUGGESTED_ARTISTS[:10]
        }
    )


@router.get("/calendar", response_class=HTMLResponse)
async def artists_calendar_page(request: Request):
    """
    アーティスト登録・カレンダー統合ページを表示（シンプル版）
    """
    try:
        return templates.TemplateResponse("simple_calendar.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"Failed to render calendar page: {e}")
        return templates.TemplateResponse("simple_calendar.html", {
            "request": request,
            "error": "ページの読み込みに失敗しました"
        })


# APIエンドポイント
@router.post("/register", response_model=ArtistResponse)
async def register_artist(
    request: ArtistRegisterRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    アーティストを登録
    """
    try:
        result = artist_service.register_artist(
            user_id=user_id,
            artist_name=request.artist_name,
            notification_enabled=request.notification_enabled
        )
        return ArtistResponse(**result['artist'])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register artist: {e}")
        raise HTTPException(status_code=500, detail="アーティストの登録に失敗しました")


@router.get("/list", response_model=ArtistListResponse)
async def list_artists(user_id: str = Depends(get_current_user_id)):
    """
    ユーザーの登録アーティスト一覧を取得
    """
    try:
        artists = artist_service.get_user_artists(user_id)
        return ArtistListResponse(
            artists=[ArtistResponse(**artist) for artist in artists],
            total=len(artists)
        )
    except Exception as e:
        logger.error(f"Failed to list artists: {e}")
        raise HTTPException(status_code=500, detail="アーティスト一覧の取得に失敗しました")


@router.delete("/{artist_id}")
async def unregister_artist(
    artist_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    アーティストの登録を解除
    """
    try:
        result = artist_service.unregister_artist(user_id, artist_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to unregister artist: {e}")
        raise HTTPException(status_code=500, detail="アーティストの登録解除に失敗しました")


@router.patch("/{artist_id}", response_model=ArtistResponse)
async def update_artist(
    artist_id: str,
    request: ArtistUpdateRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    アーティストの設定を更新
    """
    try:
        result = artist_service.update_notification_setting(
            user_id=user_id,
            artist_id=artist_id,
            enabled=request.notification_enabled
        )
        
        # 更新後のアーティスト情報を取得
        artists = artist_service.get_user_artists(user_id)
        updated_artist = next((a for a in artists if a['id'] == artist_id), None)
        
        if not updated_artist:
            raise ValueError("更新後のアーティストが見つかりません")
            
        return ArtistResponse(**updated_artist)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update artist: {e}")
        raise HTTPException(status_code=500, detail="アーティストの更新に失敗しました")


@router.get("/search", response_model=SearchResponse)
async def search_artists(q: str = ""):
    """
    アーティスト名を検索（自動補完用）
    """
    try:
        suggestions = artist_service.search_artists(q)
        return SearchResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Failed to search artists: {e}")
        raise HTTPException(status_code=500, detail="検索に失敗しました")


@router.get("/calendar-events")
async def get_calendar_events(
    user_id: str = Depends(get_current_user_id),
    days_ahead: int = 60
):
    """
    登録済みアーティストの全スケジュールを取得（カレンダー表示用）
    """
    try:
        logger.info(f"Calendar events request for user: {user_id}")
        
        # 登録済みアーティスト取得
        artists = artist_service.get_user_artists(user_id)
        
        if not artists:
            return {"events": [], "artists": [], "message": "登録されたアーティストがありません"}
        
        # 簡易版: 既存のAPIを活用してデータ取得
        all_events = []
        artist_stats = []
        
        logger.info(f"Getting calendar events for {len(artists)} artists")
        
        # 各アーティストごとに個別に収集APIを呼び出し
        for artist in artists:
            try:
                artist_name = artist['name']
                artist_id = artist['id']
                
                # 内部API呼び出しでスケジュール取得
                import requests
                
                # 内部でスケジュール収集APIを呼び出し
                internal_payload = {
                    "artist_name": artist_name,
                    "days_ahead": days_ahead,
                    "save_to_firestore": False,
                    "auto_add_to_calendar": False
                }
                
                # ローカルでScheduleCollectorを使用
                try:
                    collector = ScheduleCollector()
                    result = await collector.collect_artist_schedules(
                        artist_name=artist_name,
                        days_ahead=days_ahead
                    )
                    events = result.get('events', [])
                except ImportError as ie:
                    logger.error(f"Import error for ScheduleCollector: {ie}")
                    events = []
                except Exception as ce:
                    logger.error(f"Collection error for {artist_name}: {ce}")
                    events = []
                
                # イベントにアーティスト情報を追加
                for event in events:
                    event['artist_id'] = artist_id
                    event['notification_enabled'] = artist.get('notification_enabled', True)
                
                all_events.extend(events)
                
                artist_stats.append({
                    'id': artist_id,
                    'name': artist_name,
                    'events_count': len(events),
                    'notification_enabled': artist.get('notification_enabled', True)
                })
                
                logger.info(f"Collected {len(events)} events for {artist_name}")
                
            except Exception as e:
                logger.error(f"Failed to collect events for {artist.get('name', 'unknown')}: {e}")
                artist_stats.append({
                    'id': artist.get('id', ''),
                    'name': artist.get('name', 'unknown'),
                    'events_count': 0,
                    'notification_enabled': artist.get('notification_enabled', True),
                    'error': str(e)
                })
        
        # イベントを日付順にソート
        try:
            all_events.sort(key=lambda x: x.get('date', ''))
        except Exception as sort_error:
            logger.error(f"Failed to sort events: {sort_error}")
        
        response_data = {
            "events": all_events,
            "artists": artist_stats,
            "total_events": len(all_events),
            "total_artists": len(artists),
            "message": f"{len(artists)}件のアーティストから{len(all_events)}件のイベントを取得しました"
        }
        
        logger.info(f"Calendar events response: {len(all_events)} events from {len(artists)} artists")
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"カレンダーイベントの取得に失敗しました: {str(e)}")