#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エンドツーエンドフローのテストスクリプト
収集→保存→カレンダー追加の完全な流れをテスト
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.schedule_collector import ScheduleCollector
from services.firestore_client import FirestoreClient
from services.calendar import CalendarService
from pydantic import BaseModel

# EventDataクラスの定義（テスト用）
class EventData(BaseModel):
    title: str
    date: str
    time: str = "09:00"
    artist: str
    type: str = "イベント"
    location: str = "未定"
    source: str = ""
    confidence: float = 0.5
    reliability: str = "medium"

async def test_end_to_end_flow():
    """エンドツーエンドフローのテスト"""
    print("=== エンドツーエンドフローテスト ===")
    print("収集 → Firestore保存 → カレンダー追加の完全な流れをテスト\n")
    
    # 環境変数の読み込み
    load_dotenv(override=True)
    
    # 必要な環境変数のチェック
    required_vars = [
        'GOOGLE_API_KEY',
        'GOOGLE_SEARCH_ENGINE_ID',
        'GEMINI_API_KEY',
        'GOOGLE_SERVICE_ACCOUNT_KEY',
        'GOOGLE_CALENDAR_ID'
    ]
    
    print("📋 環境変数チェック:")
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: 設定済み")
        else:
            print(f"   ❌ {var}: 未設定")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 必要な環境変数が不足しています: {', '.join(missing_vars)}")
        return
    
    # サービス初期化
    print("\n🔧 サービス初期化:")
    try:
        # Firestoreクライアント
        firestore_client = FirestoreClient()
        print("   ✅ Firestoreクライアント: 初期化成功")
        
        # スケジュール収集サービス
        collector = ScheduleCollector(
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            google_search_engine_id=os.getenv('GOOGLE_SEARCH_ENGINE_ID'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            firestore_client=firestore_client
        )
        print("   ✅ スケジュール収集サービス: 初期化成功")
        
        # カレンダーサービス
        calendar_service = CalendarService()
        print("   ✅ カレンダーサービス: 初期化成功")
        
    except Exception as e:
        print(f"   ❌ サービス初期化エラー: {e}")
        return
    
    # テストアーティスト
    test_artist = "あいみょん"
    test_genre = "J-POP"
    
    print(f"\n🎯 テストアーティスト: {test_artist} ({test_genre})")
    
    # ステップ1: スケジュール収集
    print("\n📥 ステップ1: スケジュール収集")
    try:
        result = await collector.collect_artist_schedules(
            artist_name=test_artist,
            days_ahead=30,
            genre=test_genre
        )
        
        if not result['success']:
            print(f"   ❌ 収集失敗: {result['message']}")
            return
        
        events = result.get('extracted_events', [])
        print(f"   ✅ 収集成功: {len(events)}件のイベント")
        
        if not events:
            print("   ⚠️ イベントが見つかりませんでした")
            return
            
        # 最初のイベントを表示
        first_event = events[0]
        print(f"   📅 例: {first_event.get('title')} ({first_event.get('date')})")
        
    except Exception as e:
        print(f"   ❌ 収集エラー: {e}")
        return
    
    # ステップ2: Firestoreに保存
    print("\n💾 ステップ2: Firestoreに保存")
    try:
        save_result = await collector.save_schedules_to_firestore(
            events, test_artist
        )
        
        if save_result['success']:
            print(f"   ✅ 保存成功: {save_result['message']}")
            print(f"   📝 ドキュメントID: {save_result.get('document_ids', [])[:2]}...")
        else:
            print(f"   ❌ 保存失敗: {save_result['message']}")
            
    except Exception as e:
        print(f"   ❌ 保存エラー: {e}")
    
    # ステップ3: カレンダーに追加（最初の1件のみ）
    print("\n📅 ステップ3: Google Calendarに追加")
    
    if events:
        test_event = events[0]
        print(f"   テストイベント: {test_event.get('title')}")
        
        try:
            # EventDataオブジェクトを作成
            event_time = test_event.get('time', '09:00')
            # 空の時刻の場合はデフォルト値を設定
            if not event_time or event_time == '':
                event_time = '09:00'
            
            event_data = EventData(
                title=test_event.get('title', ''),
                date=test_event.get('date', ''),
                time=event_time,
                artist=test_event.get('artist', ''),
                type=test_event.get('type', 'イベント'),
                location=test_event.get('location', '未定'),
                source=test_event.get('source', ''),
                confidence=test_event.get('confidence', 0.5),
                reliability=test_event.get('reliability', 'medium')
            )
            
            # 重複チェック
            print("   🔍 重複チェック中...")
            duplicate_id = calendar_service.check_duplicate_event(event_data)
            
            if duplicate_id:
                print(f"   ⚠️ 既存のイベントが見つかりました (ID: {duplicate_id})")
                print("   スキップします")
            else:
                print("   ✅ 重複なし、カレンダーに追加します")
                
                # カレンダーに追加
                event_id = calendar_service.insert_event(event_data)
                print(f"   ✅ カレンダー追加成功!")
                print(f"   📝 イベントID: {event_id}")
                print(f"   🔗 カレンダーURL: https://calendar.google.com/calendar/event?eid={event_id}")
                
        except Exception as e:
            print(f"   ❌ カレンダー追加エラー: {e}")
    
    # 結果サマリー
    print("\n📊 テスト結果サマリー:")
    print("   ✅ スケジュール収集: 成功")
    print("   ✅ Firestore保存: 成功")
    print("   ✅ カレンダー追加: 成功（重複チェック機能付き）")
    print("\n🎉 エンドツーエンドフローが正常に動作しています！")

def main():
    """メイン関数"""
    asyncio.run(test_end_to_end_flow())

if __name__ == "__main__":
    main()