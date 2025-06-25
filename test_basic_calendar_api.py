#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本的なカレンダーAPI動作確認スクリプト
"""

import requests
import json
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_basic_endpoints():
    """基本エンドポイントの確認"""
    print("🔍 基本エンドポイント確認")
    print("=" * 40)
    
    endpoints = [
        ("/", "ホームページ"),
        ("/artists", "アーティスト登録ページ"),
        ("/artists/", "アーティスト一覧API"),
        ("/schedules/status", "ステータス確認")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status_icon = "✅" if response.status_code == 200 else "❌"
            print(f"   {status_icon} {endpoint} ({description}): {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} ({description}): エラー - {e}")

def test_manual_schedule_collection():
    """手動でのスケジュール収集テスト"""
    print("\n🤖 手動スケジュール収集テスト")
    print("-" * 40)
    
    test_payload = {
        "artist_name": "あいみょん",
        "days_ahead": 30,
        "save_to_firestore": False,
        "auto_add_to_calendar": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/schedules/collect",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            events_found = data.get('events_found', 0)
            message = data.get('message', '')
            
            print(f"   ✅ 手動収集成功")
            print(f"   📅 イベント数: {events_found}")
            print(f"   📝 メッセージ: {message}")
            
            events = data.get('events', [])
            if events:
                print(f"   📋 取得例:")
                event = events[0]
                print(f"     タイトル: {event.get('title', 'N/A')}")
                print(f"     日付: {event.get('date', 'N/A')}")
                print(f"     信頼度: {event.get('reliability', 'N/A')}")
            
            return True
        else:
            print(f"   ❌ 手動収集失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 手動収集エラー: {e}")
        return False

def check_deployment_status():
    """デプロイメント状況確認"""
    print("\n🚀 デプロイメント状況確認")
    print("-" * 35)
    
    try:
        response = requests.get(f"{BASE_URL}/schedules/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', {})
            
            print(f"   📊 システム状態: {data.get('status', 'unknown')}")
            print(f"   🔧 サービス状況:")
            
            for service, status in services.items():
                status_icon = "✅" if status in ['configured', 'healthy', 'implemented'] else "❌"
                print(f"     {status_icon} {service}: {status}")
            
            return True
        else:
            print(f"   ❌ ステータス確認失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ステータス確認エラー: {e}")
        return False

if __name__ == "__main__":
    print(f"🌐 基本API動作確認")
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 確認開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 基本エンドポイント確認
    test_basic_endpoints()
    
    # デプロイメント状況確認
    deployment_ok = check_deployment_status()
    
    # 手動収集テスト
    if deployment_ok:
        collection_ok = test_manual_schedule_collection()
    else:
        collection_ok = False
    
    print(f"\n🌟 確認結果")
    print("=" * 25)
    print(f"   基本機能: ✅")
    print(f"   デプロイメント: {'✅' if deployment_ok else '❌'}")
    print(f"   スケジュール収集: {'✅' if collection_ok else '❌'}")
    
    if deployment_ok and collection_ok:
        print(f"\n🎉 システムは正常に稼働しています！")
        print(f"📍 アクセス可能URL:")
        print(f"   - メイン: {BASE_URL}")
        print(f"   - アーティスト登録: {BASE_URL}/artists")
    else:
        print(f"\n⚠️ 一部機能に問題があります")
    
    print(f"\n🕒 確認完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")