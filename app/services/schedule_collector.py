# -*- coding: utf-8 -*-
"""
スケジュール収集サービス
Google Search API + Gemini抽出の統合処理
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

import httpx
from google.generativeai import GenerativeModel
import google.generativeai as genai

from config import JAPANESE_SCHEDULE_PROMPT_TEMPLATE
from utils.japanese import JapaneseTextProcessor
from services.firestore_client import FirestoreClient

logger = logging.getLogger(__name__)


class ScheduleCollector:
    """スケジュール収集・抽出・保存の統合サービス"""
    
    def __init__(self, google_api_key: str, google_search_engine_id: str, 
                 gemini_api_key: str, firestore_client: Optional[FirestoreClient] = None):
        """
        初期化
        
        Args:
            google_api_key: Google Search API キー
            google_search_engine_id: Google検索エンジンID
            gemini_api_key: Gemini API キー
            firestore_client: Firestoreクライアント
        """
        self.google_api_key = google_api_key
        self.google_search_engine_id = google_search_engine_id
        self.gemini_api_key = gemini_api_key
        self.firestore_client = firestore_client
        
        # Gemini初期化
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = GenerativeModel('gemini-1.5-flash')
        
        # 日本語処理ユーティリティ
        self.japanese_processor = JapaneseTextProcessor()
        
        logger.info("ScheduleCollector initialized")
    
    async def collect_artist_schedules(self, artist_name: str, 
                                     days_ahead: int = 30) -> Dict[str, Any]:
        """
        指定されたアーティストのスケジュール情報を収集
        
        Args:
            artist_name: アーティスト名
            days_ahead: 何日先まで検索するか
            
        Returns:
            収集結果と抽出されたスケジュール
        """
        try:
            logger.info(f"Starting schedule collection for artist: {artist_name}")
            
            # 1. Google検索でスケジュール情報を収集
            search_results = await self._search_artist_schedules(artist_name, days_ahead)
            
            if not search_results:
                return {
                    'success': False,
                    'message': f'{artist_name}のスケジュール情報が見つかりませんでした',
                    'search_results': [],
                    'extracted_events': []
                }
            
            # 2. Geminiでスケジュール情報を抽出・フィルタリング
            extracted_events = await self._extract_schedules_with_gemini(
                search_results, artist_name
            )
            
            # 3. 日本語処理とバリデーション
            validated_events = self._validate_and_normalize_events(
                extracted_events, artist_name
            )
            
            logger.info(f"Collection completed: {len(validated_events)} events found for {artist_name}")
            
            return {
                'success': True,
                'message': f'{artist_name}のスケジュール情報を{len(validated_events)}件取得しました',
                'artist_name': artist_name,
                'search_results': search_results,
                'extracted_events': validated_events,
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect schedules for {artist_name}: {e}")
            return {
                'success': False,
                'message': f'スケジュール収集中にエラーが発生しました: {str(e)}',
                'artist_name': artist_name,
                'search_results': [],
                'extracted_events': []
            }
    
    async def collect_multiple_artists_schedules(self, artist_names: List[str], 
                                               days_ahead: int = 30) -> Dict[str, Any]:
        """
        複数アーティストのスケジュール情報を並行して収集
        
        Args:
            artist_names: アーティスト名のリスト
            days_ahead: 何日先まで検索するか
            
        Returns:
            全アーティストの収集結果
        """
        try:
            logger.info(f"Starting batch collection for {len(artist_names)} artists")
            
            # 並行してスケジュール収集を実行
            tasks = [
                self.collect_artist_schedules(artist, days_ahead) 
                for artist in artist_names
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果を整理
            successful_results = []
            failed_results = []
            total_events = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_results.append({
                        'artist_name': artist_names[i],
                        'error': str(result)
                    })
                elif result.get('success'):
                    successful_results.append(result)
                    total_events += len(result.get('extracted_events', []))
                else:
                    failed_results.append(result)
            
            logger.info(f"Batch collection completed: {len(successful_results)} successful, {len(failed_results)} failed")
            
            return {
                'success': True,
                'message': f'{len(successful_results)}件のアーティストから{total_events}件のスケジュールを収集しました',
                'successful_collections': successful_results,
                'failed_collections': failed_results,
                'total_events': total_events,
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect batch schedules: {e}")
            return {
                'success': False,
                'message': f'バッチ収集中にエラーが発生しました: {str(e)}',
                'successful_collections': [],
                'failed_collections': [],
                'total_events': 0
            }
    
    async def _search_artist_schedules(self, artist_name: str, 
                                     days_ahead: int) -> List[Dict[str, str]]:
        """
        Google Search APIでアーティストのスケジュール情報を検索
        
        Args:
            artist_name: アーティスト名
            days_ahead: 何日先まで検索するか
            
        Returns:
            検索結果のリスト
        """
        try:
            # 検索クエリの生成
            current_year = datetime.now().year
            next_year = current_year + 1
            
            search_queries = [
                f"{artist_name} コンサート ライブ 2024 2025",
                f"{artist_name} スケジュール イベント {current_year} {next_year}",
                f"{artist_name} 公演 チケット 日程",
                f"{artist_name} ファンミーティング 握手会 サイン会"
            ]
            
            all_results = []
            
            async with httpx.AsyncClient() as client:
                for query in search_queries:
                    try:
                        logger.debug(f"Searching: {query}")
                        
                        response = await client.get(
                            "https://www.googleapis.com/customsearch/v1",
                            params={
                                "key": self.google_api_key,
                                "cx": self.google_search_engine_id,
                                "q": query,
                                "lr": "lang_ja",  # 日本語検索
                                "num": 5,  # 1クエリあたり5件
                                "dateRestrict": f"d{days_ahead}"  # 指定日数以内
                            },
                            timeout=10.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("items", [])
                            
                            for item in items:
                                result = {
                                    "title": item.get("title", ""),
                                    "url": item.get("link", ""),
                                    "snippet": item.get("snippet", ""),
                                    "query": query
                                }
                                all_results.append(result)
                                
                        else:
                            logger.warning(f"Search API error: {response.status_code}")
                            
                        # API制限を避けるための短い遅延
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Search query failed for '{query}': {e}")
                        continue
            
            # 重複URLを除去
            unique_results = []
            seen_urls = set()
            
            for result in all_results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)
            
            logger.info(f"Search completed: {len(unique_results)} unique results for {artist_name}")
            return unique_results[:15]  # 最大15件に制限
            
        except Exception as e:
            logger.error(f"Search failed for {artist_name}: {e}")
            return []
    
    async def _extract_schedules_with_gemini(self, search_results: List[Dict[str, str]], 
                                           artist_name: str) -> List[Dict[str, Any]]:
        """
        Gemini APIでスケジュール情報を抽出・フィルタリング
        
        Args:
            search_results: Google検索結果
            artist_name: アーティスト名
            
        Returns:
            抽出されたスケジュール情報
        """
        try:
            # 検索結果をテキストに整理
            search_text = self._format_search_results_for_gemini(search_results)
            
            # プロンプトの生成
            prompt = JAPANESE_SCHEDULE_PROMPT_TEMPLATE.format(
                artist_name=artist_name,
                search_results=search_text
            )
            
            logger.debug(f"Sending extraction request to Gemini for {artist_name}")
            
            # Gemini APIで抽出
            response = await asyncio.to_thread(
                self.gemini_model.generate_content, prompt
            )
            
            # レスポンスからJSONを抽出
            response_text = response.text.strip()
            
            # JSONの開始と終了を探す
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                
                try:
                    extracted_data = json.loads(json_text)
                    events = extracted_data.get('events', [])
                    
                    logger.info(f"Gemini extraction completed: {len(events)} events for {artist_name}")
                    return events
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Gemini JSON response: {e}")
                    logger.debug(f"Raw response: {response_text}")
                    return []
            else:
                logger.warning("No valid JSON found in Gemini response")
                logger.debug(f"Raw response: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Gemini extraction failed for {artist_name}: {e}")
            return []
    
    def _format_search_results_for_gemini(self, search_results: List[Dict[str, str]]) -> str:
        """
        検索結果をGemini用のテキスト形式に整理
        
        Args:
            search_results: Google検索結果
            
        Returns:
            整理されたテキスト
        """
        formatted_text = ""
        
        for i, result in enumerate(search_results, 1):
            title = result.get("title", "")
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            
            formatted_text += f"""
【検索結果 {i}】
タイトル: {title}
URL: {url}
概要: {snippet}

"""
        
        return formatted_text.strip()
    
    def _validate_and_normalize_events(self, events: List[Dict[str, Any]], 
                                     artist_name: str) -> List[Dict[str, Any]]:
        """
        抽出されたイベントをバリデーション・正規化
        
        Args:
            events: 抽出されたイベントリスト
            artist_name: アーティスト名
            
        Returns:
            バリデーション済みイベントリスト
        """
        validated_events = []
        
        for event in events:
            try:
                # 必須フィールドのチェック
                if not event.get('date') or not event.get('title'):
                    continue
                
                # 日本語日付の正規化
                normalized_date = self.japanese_processor.normalize_date(event.get('date', ''))
                if not normalized_date:
                    continue
                
                # 過去の日付をスキップ
                try:
                    event_date = datetime.strptime(normalized_date, '%Y-%m-%d').date()
                    if event_date < datetime.now().date():
                        continue
                except ValueError:
                    continue
                
                # 時刻の正規化
                normalized_time = self.japanese_processor.normalize_time(event.get('time', ''))
                
                # アーティスト名の確認
                event_artist = event.get('artist', artist_name)
                if artist_name.lower() not in event_artist.lower():
                    event_artist = artist_name
                
                # 信頼性とconfidenceの検証
                confidence = float(event.get('confidence', 0.5))
                reliability = event.get('reliability', 'medium')
                
                # 低信頼度をフィルタリング
                if confidence < 0.5 or reliability == 'low':
                    continue
                
                validated_event = {
                    'date': normalized_date,
                    'time': normalized_time or '',
                    'title': event.get('title', '').strip(),
                    'artist': event_artist,
                    'type': event.get('type', 'その他'),
                    'location': event.get('location', '').strip(),
                    'source': event.get('source', ''),
                    'confidence': confidence,
                    'reliability': reliability,
                    'validated_at': datetime.now().isoformat()
                }
                
                validated_events.append(validated_event)
                
            except Exception as e:
                logger.warning(f"Event validation failed: {e}")
                continue
        
        # 日付順にソート
        validated_events.sort(key=lambda x: (x['date'], x['time'] or '00:00'))
        
        logger.info(f"Validation completed: {len(validated_events)} valid events")
        return validated_events
    
    async def save_schedules_to_firestore(self, events: List[Dict[str, Any]], 
                                        artist_name: str) -> Dict[str, Any]:
        """
        収集したスケジュールをFirestoreに保存
        
        Args:
            events: 保存するイベントリスト
            artist_name: アーティスト名
            
        Returns:
            保存結果
        """
        if not self.firestore_client:
            return {
                'success': False,
                'message': 'Firestoreクライアントが利用できません',
                'saved_count': 0
            }
        
        try:
            saved_count = 0
            
            for event in events:
                try:
                    # イベントデータの準備
                    event_doc = {
                        **event,
                        'artist_name': artist_name,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Firestoreのスケジュールコレクションに保存
                    # ドキュメントID: artist_date_hash
                    import hashlib
                    doc_id_data = f"{artist_name}_{event['date']}_{event['title']}"
                    doc_id = hashlib.md5(doc_id_data.encode()).hexdigest()[:16]
                    
                    collection = self.firestore_client.db.collection('schedules')
                    collection.document(doc_id).set(event_doc)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to save event to Firestore: {e}")
                    continue
            
            logger.info(f"Saved {saved_count} events to Firestore for {artist_name}")
            
            return {
                'success': True,
                'message': f'{artist_name}のスケジュール{saved_count}件をFirestoreに保存しました',
                'saved_count': saved_count
            }
            
        except Exception as e:
            logger.error(f"Failed to save schedules to Firestore: {e}")
            return {
                'success': False,
                'message': f'Firestore保存中にエラーが発生しました: {str(e)}',
                'saved_count': 0
            }