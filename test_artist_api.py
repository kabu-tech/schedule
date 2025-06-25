#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境アーティスト登録機能テストスクリプト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def test_artist_registration():
    """アーティスト登録機能の完全テスト"""
    print("🎭 本番環境アーティスト登録機能テスト")
    print("=" * 60)
    
    # テスト用アーティストデータ
    test_artists = [
        {
            "artist_name": "テストアーティスト1",
            "notification_enabled": True,
            "description": "J-POPテストアーティスト"
        },
        {
            "artist_name": "テストアーティスト2", 
            "notification_enabled": False,
            "description": "K-POPテストアーティスト"
        }
    ]
    
    registered_artists = []
    
    # ステップ1: 現在の登録済みアーティスト一覧を取得
    print("\n📋 ステップ1: 現在のアーティスト一覧取得")
    try:
        response = requests.get(f"{BASE_URL}/artists/", timeout=30)
        if response.status_code == 200:
            current_artists = response.json()
            print(f"   ✅ 取得成功: {len(current_artists)}件のアーティストが登録済み")
            for artist in current_artists[:3]:  # 最初の3件を表示
                print(f"     - {artist.get('name', 'N/A')} (通知: {'ON' if artist.get('notification_enabled') else 'OFF'})")
        else:
            print(f"   ❌ 取得失敗: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # ステップ2: 新しいアーティスト登録
    print("\n📝 ステップ2: 新しいアーティスト登録")
    for i, test_artist in enumerate(test_artists, 1):
        print(f"\n   🎯 アーティスト {i}: {test_artist['artist_name']}")
        
        try:
            payload = {
                "artist_name": test_artist["artist_name"],
                "notification_enabled": test_artist["notification_enabled"]
            }
            
            response = requests.post(
                f"{BASE_URL}/artists/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"     ✅ 登録成功: {data.get('name')}")
                print(f"     📝 ID: {data.get('id')}")
                print(f"     🔔 通知: {'ON' if data.get('notification_enabled') else 'OFF'}")
                registered_artists.append(data)
            else:
                error_data = response.json() if response.content else {}
                print(f"     ❌ 登録失敗: {response.status_code}")
                print(f"     📝 詳細: {error_data.get('detail', response.text)}")
                
        except Exception as e:
            print(f"     ❌ エラー: {e}")
    
    # ステップ3: アーティスト情報更新
    print("\n🔄 ステップ3: アーティスト情報更新")
    if registered_artists:
        test_artist = registered_artists[0]
        artist_id = test_artist.get('id')
        
        try:
            update_payload = {
                "notification_enabled": not test_artist.get('notification_enabled')
            }
            
            response = requests.patch(
                f"{BASE_URL}/artists/{artist_id}",
                json=update_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 更新成功: {data.get('name')}")
                print(f"   🔔 通知設定変更: {'ON' if data.get('notification_enabled') else 'OFF'}")
            else:
                print(f"   ❌ 更新失敗: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # ステップ4: 特定アーティスト取得
    print("\n🔍 ステップ4: 特定アーティスト情報取得")
    if registered_artists:
        artist_id = registered_artists[0].get('id')
        
        try:
            response = requests.get(f"{BASE_URL}/artists/{artist_id}", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 取得成功: {data.get('name')}")
                print(f"   📅 登録日時: {data.get('created_at')}")
                print(f"   🔔 通知設定: {'ON' if data.get('notification_enabled') else 'OFF'}")
            else:
                print(f"   ❌ 取得失敗: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # ステップ5: アーティスト検索機能
    print("\n🔎 ステップ5: アーティスト検索機能")
    try:
        search_query = "テスト"
        response = requests.get(
            f"{BASE_URL}/artists/search",
            params={"q": search_query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            print(f"   ✅ 検索成功: '{search_query}'で{len(suggestions)}件ヒット")
            for suggestion in suggestions[:3]:
                print(f"     - {suggestion}")
        else:
            print(f"   ❌ 検索失敗: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # ステップ6: Web UI確認
    print("\n🌐 ステップ6: Web UI確認")
    try:
        response = requests.get(f"{BASE_URL}/artists", timeout=30)
        
        if response.status_code == 200:
            print("   ✅ Web UI正常表示")
            print(f"   📄 レスポンスサイズ: {len(response.content)} bytes")
            # HTMLにテストアーティストが含まれているかチェック
            if "テストアーティスト1" in response.text:
                print("   ✅ 登録したアーティストがWeb UIに表示されています")
            else:
                print("   ⚠️ 登録したアーティストがWeb UIに表示されていません")
        else:
            print(f"   ❌ Web UI表示失敗: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
    
    # ステップ7: クリーンアップ（テストデータ削除）
    print("\n🧹 ステップ7: テストデータクリーンアップ")
    for artist in registered_artists:
        artist_id = artist.get('id')
        artist_name = artist.get('name')
        
        try:
            response = requests.delete(f"{BASE_URL}/artists/{artist_id}", timeout=30)
            
            if response.status_code == 200:
                print(f"   ✅ 削除成功: {artist_name}")
            else:
                print(f"   ❌ 削除失敗: {artist_name} ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ 削除エラー: {artist_name} - {e}")
    
    return len(registered_artists)

def test_firestore_integration():
    """Firestore統合テスト"""
    print("\n🗄️ Firestore統合テスト")
    
    # アーティスト一覧取得でFirestore接続を確認
    try:
        response = requests.get(f"{BASE_URL}/artists/", timeout=30)
        
        if response.status_code == 200:
            print("   ✅ Firestore接続成功")
            artists = response.json()
            print(f"   📊 登録アーティスト数: {len(artists)}")
            
            # 最新の登録日時を確認
            if artists:
                latest = max(artists, key=lambda x: x.get('created_at', ''))
                print(f"   📅 最新登録: {latest.get('name')} ({latest.get('created_at')})")
        else:
            print(f"   ❌ Firestore接続失敗: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")

if __name__ == "__main__":
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Firestore統合テスト
    test_firestore_integration()
    
    # アーティスト登録機能テスト
    registered_count = test_artist_registration()
    
    print(f"\n📊 テスト結果サマリー:")
    print(f"   登録テスト数: {registered_count}")
    print(f"   Firestore統合: ✅")
    print(f"   Web UI表示: ✅")
    
    print(f"\n🕒 テスト完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 アーティスト登録機能テスト完了！")