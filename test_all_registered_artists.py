#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全登録アーティストのスケジュール収集テスト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_all_registered_artists():
    """登録済み全アーティストのスケジュール収集テスト"""
    print("🤖 全登録アーティストスケジュール収集テスト")
    print("=" * 60)
    
    # 登録したアーティストリスト
    test_artists = [
        {"name": "BLACKPINK", "genre": "K-POP", "expected": "高"},
        {"name": "BTS", "genre": "K-POP", "expected": "高"},
        {"name": "NewJeans", "genre": "K-POP", "expected": "高"},
        {"name": "あいみょん", "genre": "J-POP", "expected": "高"},
        {"name": "米津玄師", "genre": "J-POP", "expected": "中"},
        {"name": "Official髭男dism", "genre": "J-POP", "expected": "高"},
        {"name": "King Gnu", "genre": "J-ROCK", "expected": "高"},
        {"name": "ONE OK ROCK", "genre": "J-ROCK", "expected": "中"},
        {"name": "宝塚歌劇団", "genre": "演劇", "expected": "高"},
        {"name": "劇団四季", "genre": "演劇", "expected": "高"}
    ]
    
    collection_results = []
    total_events = 0
    
    print(f"📊 テスト対象アーティスト数: {len(test_artists)}")
    print()
    
    for i, artist_info in enumerate(test_artists, 1):
        artist_name = artist_info["name"]
        genre = artist_info["genre"]
        expected = artist_info["expected"]
        
        print(f"🎯 {i}/{len(test_artists)}: {artist_name} ({genre})")
        print(f"   予想活動レベル: {expected}")
        
        try:
            payload = {
                "artist_name": artist_name,
                "days_ahead": 60,
                "save_to_firestore": True,
                "auto_add_to_calendar": True
            }
            
            print(f"   🚀 スケジュール収集開始...")
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/schedules/collect",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                events_found = data.get('events_found', 0)
                events = data.get('events', [])
                
                collection_results.append({
                    'artist': artist_name,
                    'genre': genre,
                    'expected': expected,
                    'success': True,
                    'events_found': events_found,
                    'response_time': response_time,
                    'events': events[:2]  # 最初の2件を保存
                })
                
                total_events += events_found
                
                print(f"   ✅ 成功: {events_found}件のイベント取得")
                print(f"   ⏱️ レスポンス時間: {response_time:.2f}秒")
                
                # イベント詳細表示（最初の1件）
                if events:
                    event = events[0]
                    print(f"   📋 取得例: {event.get('title', 'N/A')}")
                    print(f"        📅 日付: {event.get('date', 'N/A')}")
                    print(f"        📊 信頼度: {event.get('reliability', 'N/A')}")
                else:
                    print(f"   📋 取得例: (なし)")
                
            else:
                error_data = response.json() if response.content else {}
                collection_results.append({
                    'artist': artist_name,
                    'genre': genre,
                    'expected': expected,
                    'success': False,
                    'events_found': 0,
                    'response_time': response_time,
                    'error': f"{response.status_code}: {error_data.get('detail', response.text)}"
                })
                print(f"   ❌ 失敗: {response.status_code}")
                
        except Exception as e:
            collection_results.append({
                'artist': artist_name,
                'genre': genre,
                'expected': expected,
                'success': False,
                'events_found': 0,
                'response_time': 0,
                'error': str(e)
            })
            print(f"   ❌ エラー: {e}")
        
        print("   " + "-" * 50)
        time.sleep(2)  # API制限回避
    
    # 結果分析
    print(f"\n📊 全体結果分析")
    print("=" * 40)
    
    successful_results = [r for r in collection_results if r['success']]
    failed_results = [r for r in collection_results if not r['success']]
    
    print(f"   総テスト数: {len(collection_results)}")
    print(f"   成功数: {len(successful_results)}")
    print(f"   成功率: {len(successful_results)/len(collection_results)*100:.1f}%")
    print(f"   総イベント数: {total_events}")
    
    if successful_results:
        avg_response_time = sum(r['response_time'] for r in successful_results) / len(successful_results)
        avg_events = sum(r['events_found'] for r in successful_results) / len(successful_results)
        print(f"   平均レスポンス時間: {avg_response_time:.2f}秒")
        print(f"   平均イベント数: {avg_events:.1f}件")
    
    # ジャンル別分析
    print(f"\n🎭 ジャンル別結果:")
    genres = {}
    for result in collection_results:
        genre = result['genre']
        if genre not in genres:
            genres[genre] = {'success': 0, 'total': 0, 'events': 0}
        genres[genre]['total'] += 1
        if result['success']:
            genres[genre]['success'] += 1
            genres[genre]['events'] += result['events_found']
    
    for genre, stats in genres.items():
        success_rate = stats['success'] / stats['total'] * 100
        status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
        print(f"   {status_icon} {genre}: {stats['success']}/{stats['total']} 成功 ({success_rate:.1f}%), {stats['events']}件のイベント")
    
    # 活動レベル別分析
    print(f"\n📈 活動レベル別結果:")
    activity_levels = {}
    for result in collection_results:
        level = result['expected']
        if level not in activity_levels:
            activity_levels[level] = {'success': 0, 'total': 0, 'events': 0}
        activity_levels[level]['total'] += 1
        if result['success']:
            activity_levels[level]['success'] += 1
            activity_levels[level]['events'] += result['events_found']
    
    for level, stats in activity_levels.items():
        success_rate = stats['success'] / stats['total'] * 100
        avg_events = stats['events'] / max(stats['success'], 1)
        print(f"   📊 {level}活動: {stats['success']}/{stats['total']} 成功, 平均{avg_events:.1f}件/アーティスト")
    
    # 最もイベントが多いアーティストTOP3
    print(f"\n🏆 イベント取得数TOP3:")
    top_artists = sorted(successful_results, key=lambda x: x['events_found'], reverse=True)[:3]
    for i, artist in enumerate(top_artists, 1):
        print(f"   {i}. {artist['artist']} ({artist['genre']}): {artist['events_found']}件")
    
    # 失敗したアーティスト
    if failed_results:
        print(f"\n❌ 収集に失敗したアーティスト:")
        for failed in failed_results:
            print(f"   - {failed['artist']} ({failed['genre']}): {failed.get('error', '不明なエラー')}")
    
    return collection_results

def generate_operation_report(results):
    """運用レポート生成"""
    print(f"\n📋 システム運用レポート")
    print("=" * 50)
    
    successful_results = [r for r in results if r['success']]
    total_events = sum(r['events_found'] for r in successful_results)
    
    # システム稼働状況評価
    success_rate = len(successful_results) / len(results) * 100
    
    if success_rate >= 90:
        status = "🟢 完全稼働"
        recommendation = "システムは正常に稼働しています。定期的な運用を開始できます。"
    elif success_rate >= 70:
        status = "🟡 良好稼働"
        recommendation = "概ね正常に稼働していますが、一部改善が必要です。"
    else:
        status = "🔴 要改善"
        recommendation = "システムの安定性に問題があります。設定を見直してください。"
    
    print(f"🎯 システム状況: {status}")
    print(f"📊 稼働率: {success_rate:.1f}%")
    print(f"📅 総イベント取得数: {total_events}件")
    print(f"📝 推奨事項: {recommendation}")
    
    # データ品質評価
    if successful_results:
        high_quality_events = 0
        for result in successful_results:
            for event in result.get('events', []):
                if event.get('reliability') == 'high':
                    high_quality_events += 1
        
        quality_rate = (high_quality_events / total_events * 100) if total_events > 0 else 0
        print(f"🌟 データ品質: {quality_rate:.1f}% (高信頼度イベント)")
    
    return {
        'status': status,
        'success_rate': success_rate,
        'total_events': total_events,
        'recommendation': recommendation
    }

if __name__ == "__main__":
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 全アーティストのスケジュール収集テスト
    results = test_all_registered_artists()
    
    # 運用レポート生成
    report = generate_operation_report(results)
    
    print(f"\n🕒 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 全アーティスト収集テスト完了！")