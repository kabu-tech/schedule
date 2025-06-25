#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
カレンダー統合UI機能テストスクリプト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_calendar_page_access():
    """カレンダーページのアクセステスト"""
    print("🌐 カレンダーページアクセステスト")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/artists/calendar", timeout=30)
        
        print(f"   📊 ステータスコード: {response.status_code}")
        print(f"   📄 レスポンスサイズ: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("   ✅ カレンダーページ正常表示")
            
            # HTMLの内容確認
            html_content = response.text
            required_elements = [
                "アーティスト登録・スケジュールカレンダー",
                "calendar-events",
                "refreshCalendar",
                "renderCalendar",
                "loadCalendarEvents"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("   ✅ 必要なUI要素がすべて含まれています")
            else:
                print(f"   ⚠️ 不足している要素: {missing_elements}")
            
            return True
        else:
            print(f"   ❌ カレンダーページ表示失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

def test_calendar_events_api():
    """カレンダーイベントAPIテスト"""
    print("\n📅 カレンダーイベントAPIテスト")
    print("-" * 40)
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/artists/calendar-events", timeout=120)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   ⏱️ レスポンス時間: {response_time:.2f}秒")
        print(f"   📊 ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            events = data.get('events', [])
            artists = data.get('artists', [])
            total_events = data.get('total_events', 0)
            total_artists = data.get('total_artists', 0)
            message = data.get('message', '')
            
            print(f"   ✅ API呼び出し成功")
            print(f"   📊 登録アーティスト数: {total_artists}")
            print(f"   📅 総イベント数: {total_events}")
            print(f"   📝 メッセージ: {message}")
            
            if events:
                print(f"   📋 取得したイベント例 (最初の3件):")
                for i, event in enumerate(events[:3], 1):
                    title = event.get('title', 'N/A')
                    date = event.get('date', 'N/A')
                    artist = event.get('artist', 'N/A')
                    reliability = event.get('reliability', 'N/A')
                    print(f"     {i}. {title}")
                    print(f"        📅 日付: {date}")
                    print(f"        🎭 アーティスト: {artist}")
                    print(f"        📊 信頼度: {reliability}")
            
            if artists:
                print(f"   🎭 アーティスト別イベント数:")
                for artist in artists[:5]:  # 最初の5件
                    name = artist.get('name', 'N/A')
                    events_count = artist.get('events_count', 0)
                    notification = '🔔' if artist.get('notification_enabled') else '🔕'
                    error = artist.get('error')
                    
                    if error:
                        print(f"     ❌ {name}: エラー ({error})")
                    else:
                        print(f"     {notification} {name}: {events_count}件")
            
            return {
                'success': True,
                'total_events': total_events,
                'total_artists': total_artists,
                'response_time': response_time
            }
            
        else:
            error_data = response.json() if response.content else {}
            print(f"   ❌ API呼び出し失敗: {response.status_code}")
            print(f"   📝 詳細: {error_data.get('detail', response.text)}")
            return {'success': False, 'error': f"{response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return {'success': False, 'error': str(e)}

def test_ui_functionality():
    """UI機能の動作テスト"""
    print("\n🖥️ UI機能動作テスト")
    print("-" * 30)
    
    # 1. 既存のアーティスト一覧確認
    try:
        response = requests.get(f"{BASE_URL}/artists/", timeout=30)
        if response.status_code == 200:
            artists = response.json()
            print(f"   ✅ アーティスト一覧取得成功: {len(artists)}件")
            
            if len(artists) >= 5:
                print("   ✅ カレンダー表示に十分なアーティスト数")
            else:
                print("   ⚠️ アーティスト数が少ないため、デモ表示になる可能性があります")
                
        else:
            print(f"   ❌ アーティスト一覧取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ アーティスト一覧取得エラー: {e}")
    
    # 2. 検索機能テスト
    try:
        test_query = "BTS"
        response = requests.get(f"{BASE_URL}/artists/search?q={test_query}", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            print(f"   ✅ 検索機能動作確認: '{test_query}' → {len(suggestions)}件の候補")
        else:
            print(f"   ❌ 検索機能エラー: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 検索機能テストエラー: {e}")

def perform_comprehensive_test():
    """統合テスト実行"""
    print("🧪 カレンダー統合UI機能 総合テスト")
    print("=" * 60)
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'calendar_page': test_calendar_page_access(),
        'calendar_api': test_calendar_events_api(),
        'ui_functionality': test_ui_functionality()
    }
    
    # 総合評価
    print(f"\n🌟 総合テスト結果")
    print("=" * 40)
    
    successful_tests = sum(1 for test, result in results.items() if 
                          (isinstance(result, bool) and result) or 
                          (isinstance(result, dict) and result.get('success')))
    
    total_tests = len(results)
    success_rate = successful_tests / total_tests * 100
    
    print(f"   成功テスト数: {successful_tests}/{total_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    
    # 各テスト結果
    test_names = {
        'calendar_page': 'カレンダーページ表示',
        'calendar_api': 'カレンダーイベントAPI',
        'ui_functionality': 'UI機能動作'
    }
    
    for test_key, result in results.items():
        test_name = test_names.get(test_key, test_key)
        if isinstance(result, bool):
            status = "✅" if result else "❌"
        elif isinstance(result, dict):
            status = "✅" if result.get('success') else "❌"
        else:
            status = "❓"
        
        print(f"   {status} {test_name}")
    
    # 推奨事項
    print(f"\n💡 次のステップ:")
    if success_rate >= 80:
        print("   🎉 カレンダー統合UI機能は正常に動作しています！")
        print("   🚀 新しいカレンダー統合ページをご利用ください:")
        print(f"   📍 {BASE_URL}/artists/calendar")
    elif success_rate >= 50:
        print("   ⚠️ 一部機能に問題があります。調査が必要です。")
    else:
        print("   ❌ 大部分の機能に問題があります。修正が必要です。")
    
    print(f"\n🕒 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

if __name__ == "__main__":
    results = perform_comprehensive_test()
    
    # API結果詳細
    api_result = results.get('calendar_api')
    if isinstance(api_result, dict) and api_result.get('success'):
        print(f"\n📊 カレンダーAPI詳細:")
        print(f"   📅 総イベント数: {api_result.get('total_events', 0)}")
        print(f"   🎭 総アーティスト数: {api_result.get('total_artists', 0)}")
        print(f"   ⏱️ レスポンス時間: {api_result.get('response_time', 0):.2f}秒")