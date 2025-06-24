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

logger = logging.getLogger(__name__)

# ルーターの作成
router = APIRouter(
    prefix="/artists",
    tags=["artists"],
    responses={404: {"description": "Not found"}},
)

# テンプレートの設定
templates = Jinja2Templates(directory="app/templates")

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