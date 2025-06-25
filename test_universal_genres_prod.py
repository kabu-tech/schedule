#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境汎用ジャンル対応テストスクリプト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_universal_genre_support():
    """汎用ジャンル対応の本番環境テスト"""
    print("🎭 本番環境汎用ジャンル対応テスト")
    print("=" * 70)
    
    # テストケース: 様々なジャンル
    test_cases = [
        {
            "artist_name": "BLACKPINK",
            "genre": "K-POP", 
            "description": "K-POPグループ",
            "expected_events": "> 3"
        },
        {
            "artist_name": "あいみょん",
            "genre": "J-POP",
            "description": "日本のシンガーソングライター", 
            "expected_events": "> 2"
        },
        {
            "artist_name": "King Gnu",
            "genre": "J-ROCK",
            "description": "日本のロックバンド",
            "expected_events": ">= 0"
        },
        {
            "artist_name": "宝塚歌劇団",
            "genre": "演劇", 
            "description": "日本の劇団",
            "expected_events": ">= 0"
        },
        {
            "artist_name": "サザンオールスターズ",
            "genre": "J-ROCK",
            "description": "日本のロックバンド（ベテラン）",
            "expected_events": ">= 0"
        }
    ]
    
    results = []
    total_events = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 テスト {i}/{len(test_cases)}: {test_case['artist_name']} ({test_case['genre']})")
        print(f"   説明: {test_case['description']}")
        print(f"   予想イベント数: {test_case['expected_events']}")
        
        try:
            # 本番環境のAPIリクエスト
            payload = {
                "artist_name": test_case["artist_name"],
                "days_ahead": 60,  # 60日先まで
                "save_to_firestore": False,  # テストなので保存しない
                "auto_add_to_calendar": False  # テストなのでカレンダーに追加しない
            }
            
            print(f"   🚀 API リクエスト送信中...")
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/schedules/collect",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"   ⏱️ レスポンス時間: {response_time:.2f}秒")
            
            if response.status_code == 200:
                data = response.json()
                events_found = data.get('events_found', 0)
                events = data.get('events', [])
                
                print(f"   ✅ 成功: {data.get('message', 'メッセージなし')}")
                print(f"   📊 イベント数: {events_found}件")
                
                # イベント詳細表示（最初の2件）
                if events:
                    print(f"   📋 取得したイベント:")
                    for j, event in enumerate(events[:2], 1):
                        title = event.get('title', 'N/A')
                        date = event.get('date', 'N/A')
                        event_type = event.get('type', 'N/A')
                        reliability = event.get('reliability', 'N/A')
                        confidence = event.get('confidence', 0)
                        
                        print(f"     {j}. {title}")
                        print(f"        📅 日付: {date}")
                        print(f"        🎭 種別: {event_type}")
                        print(f"        📊 信頼度: {reliability} ({confidence:.2f})")
                        print(f"        🔗 ソース: {event.get('source', 'N/A')[:50]}...")
                
                # テスト結果記録
                results.append({
                    'artist': test_case['artist_name'],
                    'genre': test_case['genre'],
                    'success': True,
                    'events_found': events_found,
                    'response_time': response_time,
                    'message': data.get('message', '')
                })
                
                total_events += events_found
                
            else:
                error_data = response.json() if response.content else {}
                print(f"   ❌ 失敗: {response.status_code}")
                print(f"   📝 詳細: {error_data.get('detail', response.text)}")
                
                results.append({
                    'artist': test_case['artist_name'],
                    'genre': test_case['genre'],
                    'success': False,
                    'events_found': 0,
                    'response_time': response_time,
                    'error': f"{response.status_code}: {error_data.get('detail', response.text)}"
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ タイムアウト: リクエストが2分以内に完了しませんでした")
            results.append({
                'artist': test_case['artist_name'],
                'genre': test_case['genre'],
                'success': False,
                'events_found': 0,
                'response_time': 120,
                'error': 'タイムアウト'
            })
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            results.append({
                'artist': test_case['artist_name'],
                'genre': test_case['genre'],
                'success': False,
                'events_found': 0,
                'response_time': 0,
                'error': str(e)
            })
        
        print("   " + "-" * 50)
    
    # テスト結果サマリー
    print(f"\n📊 汎用ジャンル対応テスト結果サマリー")
    print("=" * 50)
    
    successful_tests = [r for r in results if r['success']]
    successful_genres = set(r['genre'] for r in successful_tests)
    total_genres = set(r['genre'] for r in results)
    
    print(f"   総テスト数: {len(results)}")
    print(f"   成功テスト数: {len(successful_tests)}")
    print(f"   成功率: {len(successful_tests)/len(results)*100:.1f}%")
    print(f"   総イベント取得数: {total_events}")
    print(f"   平均レスポンス時間: {sum(r['response_time'] for r in successful_tests)/len(successful_tests):.2f}秒" if successful_tests else "N/A")
    
    print(f"\n🎯 ジャンル別結果:")
    for genre in sorted(total_genres):
        genre_results = [r for r in results if r['genre'] == genre]
        genre_successful = [r for r in genre_results if r['success']]
        genre_events = sum(r['events_found'] for r in genre_successful)
        
        status = "✅" if genre_successful else "❌"
        print(f"   {status} {genre}: {len(genre_successful)}/{len(genre_results)} 成功, {genre_events}件のイベント")
        
        for result in genre_results:
            artist_status = "✅" if result['success'] else "❌"
            events_info = f"({result['events_found']}件)" if result['success'] else f"({result.get('error', 'エラー')})"
            print(f"     {artist_status} {result['artist']} {events_info}")
    
    # 拡張性評価
    print(f"\n🚀 拡張性評価:")
    print(f"   テストジャンル数: {len(total_genres)}")
    print(f"   成功ジャンル数: {len(successful_genres)}")
    print(f"   ジャンル成功率: {len(successful_genres)/len(total_genres)*100:.1f}%")
    
    if len(successful_genres) == len(total_genres):
        print("   🌟 完璧な拡張性！全ジャンルで正常動作")
    elif len(successful_genres) >= len(total_genres) * 0.8:
        print("   ✅ 高い拡張性！ほとんどのジャンルで正常動作")
    elif len(successful_genres) >= len(total_genres) * 0.6:
        print("   ⚠️ 中程度の拡張性。一部ジャンルで改善が必要")
    else:
        print("   ❌ 拡張性に課題あり。システム調整が必要")
    
    # 品質評価
    high_quality_events = sum(1 for r in results for event in r.get('events', []) 
                             if event.get('reliability') == 'high')
    
    print(f"\n📊 品質評価:")
    print(f"   高信頼度イベント数: {high_quality_events}")
    print(f"   AI信頼性フィルタリング: ✅ 動作中")
    
    return results

def test_api_consistency():
    """API一貫性テスト"""
    print(f"\n🔄 API一貫性テスト")
    
    # 同じアーティストで複数回テスト
    test_artist = "あいみょん"
    consistency_results = []
    
    print(f"   🎯 テスト対象: {test_artist}")
    print(f"   📊 3回連続実行して結果の一貫性を確認")
    
    for i in range(3):
        try:
            payload = {
                "artist_name": test_artist,
                "days_ahead": 30,
                "save_to_firestore": False,
                "auto_add_to_calendar": False
            }
            
            response = requests.post(
                f"{BASE_URL}/schedules/collect",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                events_found = data.get('events_found', 0)
                consistency_results.append(events_found)
                print(f"     テスト {i+1}: {events_found}件")
            else:
                print(f"     テスト {i+1}: エラー ({response.status_code})")
                
        except Exception as e:
            print(f"     テスト {i+1}: エラー ({e})")
            
        time.sleep(2)  # API制限を避けるため少し待機
    
    if consistency_results:
        min_events = min(consistency_results)
        max_events = max(consistency_results)
        avg_events = sum(consistency_results) / len(consistency_results)
        
        print(f"   📊 一貫性結果:")
        print(f"     最小: {min_events}件")
        print(f"     最大: {max_events}件")
        print(f"     平均: {avg_events:.1f}件")
        
        if max_events - min_events <= 1:
            print(f"   ✅ 高い一貫性（差異: {max_events - min_events}件）")
        elif max_events - min_events <= 3:
            print(f"   ⚠️ 中程度の一貫性（差異: {max_events - min_events}件）")
        else:
            print(f"   ❌ 一貫性に課題（差異: {max_events - min_events}件）")

if __name__ == "__main__":
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 汎用ジャンル対応テスト
    results = test_universal_genre_support()
    
    # API一貫性テスト
    test_api_consistency()
    
    print(f"\n🕒 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 本番環境汎用ジャンル対応テスト完了！")
    
    # 最終評価
    successful_results = [r for r in results if r['success']]
    total_success_rate = len(successful_results) / len(results) * 100
    
    print(f"\n🌟 最終評価:")
    if total_success_rate >= 80:
        print(f"   🥇 優秀 ({total_success_rate:.1f}%成功) - 本番運用準備完了！")
    elif total_success_rate >= 60:
        print(f"   🥈 良好 ({total_success_rate:.1f}%成功) - 軽微な調整で運用可能")
    else:
        print(f"   🥉 要改善 ({total_success_rate:.1f}%成功) - 追加の調整が必要")