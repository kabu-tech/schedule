#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境APIテストスクリプト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_schedule_collection():
    """スケジュール収集APIのテスト"""
    print("🧪 本番環境スケジュール収集APIテスト")
    print("=" * 50)
    
    # テストケース
    test_cases = [
        {
            "artist_name": "あいみょん",
            "days_ahead": 30,
            "save_to_firestore": True,
            "auto_add_to_calendar": False,
            "description": "J-POPアーティストのテスト"
        },
        {
            "artist_name": "BLACKPINK", 
            "days_ahead": 60,
            "save_to_firestore": True,
            "auto_add_to_calendar": False,
            "description": "K-POPグループのテスト"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 テスト {i}: {test_case['description']}")
        print(f"   アーティスト: {test_case['artist_name']}")
        
        try:
            # APIリクエスト
            url = f"{BASE_URL}/schedules/collect"
            
            payload = {
                "artist_name": test_case["artist_name"],
                "days_ahead": test_case["days_ahead"], 
                "save_to_firestore": test_case["save_to_firestore"],
                "auto_add_to_calendar": test_case["auto_add_to_calendar"]
            }
            
            print(f"   🚀 リクエスト送信中...")
            start_time = time.time()
            
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # 2分のタイムアウト
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"   ⏱️ レスポンス時間: {response_time:.2f}秒")
            print(f"   📊 ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功: {data.get('message', 'メッセージなし')}")
                print(f"   📅 イベント数: {data.get('events_found', 0)}")
                
                # 最初の2件を表示
                events = data.get('events', [])
                for j, event in enumerate(events[:2], 1):
                    print(f"     {j}. {event.get('title', 'N/A')}")
                    print(f"        📅 日付: {event.get('date', 'N/A')}")
                    print(f"        🎭 種別: {event.get('type', 'N/A')}")
                    print(f"        📊 信頼度: {event.get('reliability', 'N/A')}")
                
            else:
                print(f"   ❌ エラー: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 詳細: {error_data.get('detail', response.text)}")
                except:
                    print(f"   📝 詳細: {response.text}")
                    
        except requests.exceptions.Timeout:
            print(f"   ⏰ タイムアウト: リクエストが2分以内に完了しませんでした")
        except requests.exceptions.RequestException as e:
            print(f"   🚫 リクエストエラー: {e}")
        except Exception as e:
            print(f"   ❌ 予期しないエラー: {e}")
        
        print("   " + "-" * 40)

def test_status_endpoint():
    """ステータスエンドポイントのテスト"""
    print("\n🔍 ステータスエンドポイントテスト")
    try:
        response = requests.get(f"{BASE_URL}/schedules/status", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ ステータス確認成功")
            print(f"   📊 システム状態: {data.get('status')}")
            
            services = data.get('services', {})
            for service, status in services.items():
                status_icon = "✅" if status in ['configured', 'healthy'] else "❌"
                print(f"   {status_icon} {service}: {status}")
        else:
            print(f"   ❌ ステータス確認失敗: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ステータス確認エラー: {e}")

if __name__ == "__main__":
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ステータス確認
    test_status_endpoint()
    
    # スケジュール収集テスト
    test_schedule_collection()
    
    print(f"\n🕒 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 本番環境APIテスト完了！")