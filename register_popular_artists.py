#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人気アーティスト本番環境登録スクリプト
"""

import requests
import json
import time
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"

def register_popular_artists():
    """人気アーティストを本番環境に登録"""
    print("🎭 人気アーティスト本番環境登録")
    print("=" * 60)
    
    # 人気アーティストリスト（各ジャンルから厳選）
    popular_artists = [
        # K-POP
        {
            "artist_name": "BLACKPINK",
            "notification_enabled": True,
            "description": "世界的人気K-POPガールズグループ",
            "genre": "K-POP",
            "expected_activity": "高"
        },
        {
            "artist_name": "BTS",
            "notification_enabled": True,
            "description": "グローバルK-POPボーイズグループ",
            "genre": "K-POP",
            "expected_activity": "高"
        },
        {
            "artist_name": "NewJeans",
            "notification_enabled": True,
            "description": "人気急上昇K-POPグループ",
            "genre": "K-POP",
            "expected_activity": "高"
        },
        
        # J-POP
        {
            "artist_name": "あいみょん",
            "notification_enabled": True,
            "description": "人気シンガーソングライター",
            "genre": "J-POP",
            "expected_activity": "高"
        },
        {
            "artist_name": "米津玄師",
            "notification_enabled": True,
            "description": "トップアーティスト",
            "genre": "J-POP",
            "expected_activity": "中"
        },
        {
            "artist_name": "Official髭男dism",
            "notification_enabled": True,
            "description": "人気J-POPバンド",
            "genre": "J-POP",
            "expected_activity": "高"
        },
        
        # J-ROCK
        {
            "artist_name": "King Gnu",
            "notification_enabled": True,
            "description": "人気ロックバンド",
            "genre": "J-ROCK",
            "expected_activity": "高"
        },
        {
            "artist_name": "ONE OK ROCK",
            "notification_enabled": True,
            "description": "世界的ロックバンド",
            "genre": "J-ROCK",
            "expected_activity": "中"
        },
        
        # 演劇・エンターテイメント
        {
            "artist_name": "宝塚歌劇団",
            "notification_enabled": True,
            "description": "日本の代表的劇団",
            "genre": "演劇",
            "expected_activity": "高"
        },
        {
            "artist_name": "劇団四季",
            "notification_enabled": True,
            "description": "日本最大のミュージカル劇団",
            "genre": "演劇",
            "expected_activity": "高"
        }
    ]
    
    registered_artists = []
    failed_artists = []
    
    print(f"📊 登録予定アーティスト数: {len(popular_artists)}")
    print()
    
    for i, artist_info in enumerate(popular_artists, 1):
        print(f"🎯 {i}/{len(popular_artists)}: {artist_info['artist_name']} ({artist_info['genre']})")
        print(f"   説明: {artist_info['description']}")
        print(f"   予想活動レベル: {artist_info['expected_activity']}")
        
        try:
            # アーティスト登録APIリクエスト
            payload = {
                "artist_name": artist_info["artist_name"],
                "notification_enabled": artist_info["notification_enabled"]
            }
            
            response = requests.post(
                f"{BASE_URL}/artists/register",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                artist_id = data.get('id')
                
                # 登録情報を拡張
                registration_data = {
                    **data,
                    'genre': artist_info['genre'],
                    'description': artist_info['description'],
                    'expected_activity': artist_info['expected_activity']
                }
                
                registered_artists.append(registration_data)
                print(f"   ✅ 登録成功: ID {artist_id}")
                print(f"   🔔 通知: {'ON' if data.get('notification_enabled') else 'OFF'}")
                
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('detail', response.text)
                
                failed_artists.append({
                    'artist': artist_info['artist_name'],
                    'error': f"{response.status_code}: {error_message}"
                })
                
                print(f"   ❌ 登録失敗: {response.status_code}")
                print(f"   📝 詳細: {error_message}")
                
        except Exception as e:
            failed_artists.append({
                'artist': artist_info['artist_name'],
                'error': str(e)
            })
            print(f"   ❌ エラー: {e}")
        
        print("   " + "-" * 50)
        time.sleep(1)  # API制限回避
    
    # 登録結果サマリー
    print("\n📊 アーティスト登録結果")
    print("=" * 40)
    print(f"   総登録試行数: {len(popular_artists)}")
    print(f"   成功登録数: {len(registered_artists)}")
    print(f"   失敗数: {len(failed_artists)}")
    print(f"   成功率: {len(registered_artists)/len(popular_artists)*100:.1f}%")
    
    # ジャンル別サマリー
    if registered_artists:
        print("\n🎭 ジャンル別登録結果:")
        genres = {}
        for artist in registered_artists:
            genre = artist.get('genre', '不明')
            if genre not in genres:
                genres[genre] = []
            genres[genre].append(artist['name'])
        
        for genre, artists in genres.items():
            print(f"   🎵 {genre}: {len(artists)}件")
            for artist_name in artists:
                print(f"     - {artist_name}")
    
    # 失敗したアーティスト
    if failed_artists:
        print("\n❌ 登録に失敗したアーティスト:")
        for failed in failed_artists:
            print(f"   - {failed['artist']}: {failed['error']}")
    
    return registered_artists, failed_artists

def verify_artist_registration():
    """登録されたアーティストの確認"""
    print("\n🔍 登録アーティスト確認")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/artists/", timeout=30)
        
        if response.status_code == 200:
            artists = response.json()
            print(f"   ✅ 現在の登録アーティスト数: {len(artists)}")
            
            # 最新の10件を表示
            latest_artists = sorted(artists, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
            print(f"   📋 最新登録アーティスト (最新10件):")
            
            for i, artist in enumerate(latest_artists, 1):
                created_at = artist.get('created_at', 'N/A')
                notification = '🔔' if artist.get('notification_enabled') else '🔕'
                print(f"     {i:2d}. {artist.get('name', 'N/A')} {notification}")
                print(f"         登録日: {created_at}")
            
            return len(artists)
        else:
            print(f"   ❌ 確認失敗: {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return 0

def test_schedule_collection_for_registered():
    """登録したアーティストのスケジュール収集テスト"""
    print("\n🤖 登録アーティストのスケジュール収集テスト")
    print("-" * 50)
    
    # テスト対象アーティスト（登録済みから選択）
    test_artists = [
        {"name": "あいみょん", "genre": "J-POP"},
        {"name": "BLACKPINK", "genre": "K-POP"},
        {"name": "King Gnu", "genre": "J-ROCK"}
    ]
    
    collection_results = []
    
    for artist_info in test_artists:
        artist_name = artist_info["name"]
        genre = artist_info["genre"]
        
        print(f"\n🎯 テスト: {artist_name} ({genre})")
        
        try:
            payload = {
                "artist_name": artist_name,
                "days_ahead": 60,
                "save_to_firestore": True,
                "auto_add_to_calendar": True  # カレンダー自動追加も有効
            }
            
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
                
                collection_results.append({
                    'artist': artist_name,
                    'genre': genre,
                    'success': True,
                    'events_found': events_found,
                    'response_time': response_time
                })
                
                print(f"   ✅ 成功: {events_found}件のイベント取得")
                print(f"   ⏱️ レスポンス時間: {response_time:.2f}秒")
                print(f"   💾 Firestore保存: ON")
                print(f"   📅 カレンダー追加: ON")
                
            else:
                collection_results.append({
                    'artist': artist_name,
                    'genre': genre,
                    'success': False,
                    'events_found': 0,
                    'response_time': response_time,
                    'error': f"{response.status_code}"
                })
                print(f"   ❌ 失敗: {response.status_code}")
                
        except Exception as e:
            collection_results.append({
                'artist': artist_name,
                'genre': genre,
                'success': False,
                'events_found': 0,
                'response_time': 0,
                'error': str(e)
            })
            print(f"   ❌ エラー: {e}")
    
    # 収集結果サマリー
    print(f"\n📊 スケジュール収集テスト結果:")
    successful_collections = [r for r in collection_results if r['success']]
    total_events = sum(r['events_found'] for r in successful_collections)
    
    print(f"   成功率: {len(successful_collections)}/{len(collection_results)} = {len(successful_collections)/len(collection_results)*100:.1f}%")
    print(f"   総イベント数: {total_events}件")
    
    if successful_collections:
        avg_response_time = sum(r['response_time'] for r in successful_collections) / len(successful_collections)
        print(f"   平均レスポンス時間: {avg_response_time:.2f}秒")
    
    return collection_results

if __name__ == "__main__":
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: 人気アーティスト登録
    registered_artists, failed_artists = register_popular_artists()
    
    # Step 2: 登録確認
    total_artists = verify_artist_registration()
    
    # Step 3: スケジュール収集テスト
    if registered_artists:
        collection_results = test_schedule_collection_for_registered()
    
    # 最終サマリー
    print(f"\n🌟 システム運用開始サマリー")
    print("=" * 50)
    print(f"   登録アーティスト数: {len(registered_artists)}")
    print(f"   総データベース登録数: {total_artists}")
    
    if registered_artists:
        successful_collections = [r for r in collection_results if r['success']]
        print(f"   動作確認済みアーティスト: {len(successful_collections)}")
        print(f"   システム稼働状況: {'🟢 正常稼働' if len(successful_collections) >= 2 else '🟡 部分稼働'}")
    
    print(f"\n🕒 完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 システム運用開始準備完了！")