# -*- coding: utf-8 -*-
"""
Firestoreを使用したイベント保存エンドポイント
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from google.cloud import firestore

logger = logging.getLogger(__name__)

router = APIRouter()


class EventData(BaseModel):
    """イベントデータモデル"""
    date: str = Field(..., description="イベント日付 (YYYY-MM-DD)")
    time: str = Field(..., description="イベント時間 (HH:MM)")
    title: str = Field(..., description="イベントタイトル")
    artist: str = Field(..., description="アーティスト名")
    type: str = Field(..., description="イベント種別")
    location: str = Field(..., description="開催場所")
    source: str = Field(..., description="情報源URL")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信頼度")
    reliability: str = Field(..., description="信頼性レベル")
    
    @validator('date')
    def validate_date_format(cls, v):
        """日付フォーマットの検証"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('日付は YYYY-MM-DD 形式で入力してください')
    
    @validator('time')
    def validate_time_format(cls, v):
        """時間フォーマットの検証（空文字許可）"""
        if v == "":
            return v
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('時間は HH:MM 形式で入力してください')


class SaveResponse(BaseModel):
    """保存レスポンス"""
    id: str
    message: str


@router.post("/events/save", response_model=SaveResponse, status_code=201)
async def save_event(event: EventData) -> SaveResponse:
    """
    イベントデータをFirestoreに保存
    
    Args:
        event: 保存するイベントデータ
        
    Returns:
        保存結果（ID、メッセージ）
    """
    try:
        # Firestore初期化
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.error("GOOGLE_CLOUD_PROJECT not found in environment variables")
            raise HTTPException(status_code=500, detail="Firestore設定エラー")
        
        # Firestoreクライアント作成
        db = firestore.Client(project=project_id)
        
        # イベントデータを辞書に変換
        event_dict = event.dict()
        
        # タイムスタンプ追加
        event_dict['created_at'] = datetime.utcnow()
        event_dict['updated_at'] = datetime.utcnow()
        
        # UUIDを生成してドキュメントIDとして使用
        event_id = str(uuid.uuid4())
        
        # Firestoreに保存
        doc_ref = db.collection('events').document(event_id)
        doc_ref.set(event_dict)
        
        logger.info(f"Event saved successfully with ID: {event_id}")
        
        return SaveResponse(
            id=event_id,
            message=f"イベント '{event.title}' が正常に保存されました"
        )
        
    except ValueError as e:
        # バリデーションエラー
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # その他のエラー
        logger.error(f"Firestore save error: {e}")
        raise HTTPException(status_code=500, detail="イベント保存エラー")