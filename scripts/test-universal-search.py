#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汎用検索+AI信頼性判定のテストスクリプト
ジャンル拡張性をテスト
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.schedule_collector import ScheduleCollector
from services.firestore_client import FirestoreClient

async def test_genre_expansion():
    """様々なジャンルでのスケジュール収集をテスト"""
    print("=== 汎用検索+AI信頼性判定テスト ===")
    
    # 環境変数の読み込み
    load_dotenv(override=True)
    
    # サービス初期化
    try:
        firestore_client = FirestoreClient()
        collector = ScheduleCollector(
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            google_search_engine_id=os.getenv('GOOGLE_SEARCH_ENGINE_ID'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            firestore_client=firestore_client
        )
    except Exception as e:
        print(f"❌ サービス初期化エラー: {e}")
        return
    
    # テストケース: 様々なジャンル
    test_cases = [
        {
            "artist": "BLACKPINK",
            "genre": "K-POP",
            "description": "K-POPグループ"
        },
        {
            "artist": "あいみょん", 
            "genre": "J-POP",
            "description": "日本のシンガーソングライター"
        },
        {
            "artist": "King Gnu",
            "genre": "J-ROCK", 
            "description": "日本のロックバンド"
        },
        {
            "artist": "宝塚歌劇団",
            "genre": "演劇",
            "description": "日本の劇団"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🎯 テスト: {test_case['artist']} ({test_case['genre']})")
        print(f"   説明: {test_case['description']}")
        
        try:
            result = await collector.collect_artist_schedules(
                artist_name=test_case['artist'],
                days_ahead=60,
                genre=test_case['genre']
            )
            
            print(f"   結果: {'✅ 成功' if result['success'] else '❌ 失敗'}")
            print(f"   メッセージ: {result['message']}")
            
            if result['success']:
                events = result.get('extracted_events', [])
                print(f"   イベント数: {len(events)}")
                
                # 最初の2件を表示
                for i, event in enumerate(events[:2], 1):
                    print(f"     {i}. {event.get('title', 'N/A')}")
                    print(f"        日付: {event.get('date', 'N/A')}")
                    print(f"        信頼度: {event.get('reliability', 'N/A')}")
                    print(f"        ソース: {event.get('source', 'N/A')}")
            
            results.append({
                'test_case': test_case,
                'success': result['success'],
                'event_count': len(result.get('extracted_events', []))
            })
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            results.append({
                'test_case': test_case,
                'success': False,
                'event_count': 0,
                'error': str(e)
            })
        
        print("   " + "="*50)
    
    # 結果サマリー
    print(f"\n📊 テスト結果サマリー")
    print(f"   総テスト数: {len(results)}")
    
    successful = [r for r in results if r['success']]
    print(f"   成功: {len(successful)}")
    
    total_events = sum(r['event_count'] for r in results)
    print(f"   総イベント数: {total_events}")
    
    print(f"\n🎯 ジャンル別結果:")
    for result in results:
        test_case = result['test_case']
        status = "✅" if result['success'] else "❌"
        events = result['event_count']
        print(f"   {status} {test_case['genre']}: {test_case['artist']} ({events}件)")
    
    # 拡張性評価
    print(f"\n🚀 拡張性評価:")
    genres_tested = set(r['test_case']['genre'] for r in results)
    genres_successful = set(r['test_case']['genre'] for r in results if r['success'])
    
    print(f"   テストジャンル数: {len(genres_tested)}")
    print(f"   成功ジャンル数: {len(genres_successful)}")
    print(f"   拡張性スコア: {len(genres_successful)}/{len(genres_tested)} ({len(genres_successful)/len(genres_tested)*100:.1f}%)")
    
    if len(genres_successful) >= 3:
        print("   ✅ 高い拡張性を確認！様々なジャンルに対応可能")
    elif len(genres_successful) >= 2:
        print("   ⚠️ 中程度の拡張性。一部ジャンルで改善が必要")
    else:
        print("   ❌ 拡張性に課題あり。プロンプト調整が必要")

def main():
    """メイン関数"""
    asyncio.run(test_genre_expansion())

if __name__ == "__main__":
    main()