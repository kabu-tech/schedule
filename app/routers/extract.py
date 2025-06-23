# -*- coding: utf-8 -*-
"""
Gemini APIを使用したスケジュール情報抽出エンドポイント
"""

import os
import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

logger = logging.getLogger(__name__)

router = APIRouter()


class SourceItem(BaseModel):
    """検索結果の項目"""
    title: str
    url: str
    snippet: str


class ExtractRequest(BaseModel):
    """抽出リクエスト"""
    sources: List[SourceItem]


class ExtractResponse(BaseModel):
    """抽出レスポンス"""
    events: List[Dict[str, Any]]


@router.post("/extract", response_model=ExtractResponse)
async def extract_schedules(request: ExtractRequest) -> ExtractResponse:
    """
    検索結果からスケジュール情報を抽出
    
    Args:
        request: 検索結果のリスト
        
    Returns:
        抽出されたスケジュール情報
    """
    # バリデーション
    if not request.sources:
        raise HTTPException(status_code=400, detail="sourcesが空です")
    
    # Gemini API設定
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise HTTPException(status_code=500, detail="API設定エラー")
    
    try:
        # Gemini APIの初期化
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 検索結果をテキストに変換
        search_text = "\n\n".join([
            f"タイトル: {item.title}\nURL: {item.url}\n内容: {item.snippet}"
            for item in request.sources
        ])
        
        # プロンプト作成
        prompt = f"""
以下の検索結果から、信頼性の高いK-POPスケジュール情報のみを抽出してください。

【信頼性判定基準】
高信頼度：
- 公式サイト（.com、.jp、.kr等で「official」「artist名」を含むドメイン）
- 大手メディア（NHK、朝日新聞、音楽ナタリーなど）
- 公式チケットサイト（e+、チケットぴあ、ローソンチケットなど）
- 行政機関の発表

低信頼度（無視する）：
- 個人ブログ・まとめサイト
- 「〜かも」「〜らしい」「噂」「予想」を含む投稿
- 匿名掲示板・SNSの非公式投稿
- 「未確認」「リーク」を含む情報

【抽出ルール】
1. 明確な日付が記載されているもののみ
2. 過去の日付は除外
3. 信頼度0.7未満の情報は除外
4. 重複する情報は信頼度の高いものを優先

【検索結果】
{search_text}

【出力形式】
以下のJSON形式で出力してください：
{{
    "events": [
        {{
            "date": "YYYY-MM-DD",
            "time": "HH:MM",
            "title": "イベント名",
            "artist": "アーティスト名", 
            "type": "コンサート|リリース|テレビ出演|ラジオ出演|イベント|その他",
            "location": "開催場所",
            "source": "https://...",
            "confidence": 0.9,
            "reliability": "high|medium|low"
        }}
    ]
}}

信頼性が低い場合は結果を空の配列で返してください。
"""
        
        # Gemini APIに送信
        response = model.generate_content(prompt)
        
        # レスポンスをパース
        try:
            # JSONブロックを抽出
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif response_text.startswith("{"):
                json_text = response_text
            else:
                # JSONが見つからない場合
                json_text = '{"events": []}'
            
            result = json.loads(json_text)
            events = result.get("events", [])
            
            return ExtractResponse(events=events)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response.text}")
            return ExtractResponse(events=[])
            
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=500, detail="スケジュール抽出エラー")