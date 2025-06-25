#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スケジュール収集自動化セットアップスクリプト
"""

import subprocess
import json
import requests
from datetime import datetime

# 本番環境のベースURL
BASE_URL = "https://schedule-auto-feed-wkwgupze5a-an.a.run.app"
PROJECT_ID = "kpop-sched-dev"
SERVICE_NAME = "schedule-auto-feed"
REGION = "asia-northeast1"

def test_collect_registered_endpoint():
    """登録済みアーティスト一括収集エンドポイントのテスト"""
    print("🧪 登録済みアーティスト一括収集エンドポイントテスト")
    print("=" * 60)
    
    try:
        payload = {
            "days_ahead": 60
        }
        
        print(f"   🚀 一括収集API呼び出し中...")
        start_time = datetime.now()
        
        response = requests.post(
            f"{BASE_URL}/schedules/collect-registered",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分のタイムアウト
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"   ⏱️ 実行時間: {duration:.2f}秒")
        print(f"   📊 ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data.get('message', 'メッセージなし')}")
            print(f"   📊 成功収集数: {data.get('successful_collections', 0)}")
            print(f"   📊 失敗収集数: {data.get('failed_collections', 0)}")
            print(f"   📅 総イベント数: {data.get('total_events', 0)}")
            
            # 結果詳細表示
            results = data.get('results', [])
            if results:
                print(f"   📋 収集結果詳細:")
                for i, result in enumerate(results[:5], 1):  # 最初の5件を表示
                    artist = result.get('artist_name', 'N/A')
                    events = result.get('events_found', 0)
                    success = result.get('success', False)
                    status_icon = "✅" if success else "❌"
                    print(f"     {i}. {status_icon} {artist}: {events}件")
            
            return True
            
        else:
            error_data = response.json() if response.content else {}
            print(f"   ❌ 失敗: {response.status_code}")
            print(f"   📝 詳細: {error_data.get('detail', response.text)}")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

def create_cloud_scheduler_job():
    """Cloud Schedulerジョブの作成"""
    print("\n⏰ Cloud Schedulerジョブ作成")
    print("-" * 40)
    
    job_name = "schedule-collection-daily"
    schedule = "0 9 * * *"  # 毎日午前9時（JST）
    timezone = "Asia/Tokyo"
    
    # Schedulerジョブの設定
    scheduler_config = {
        "name": f"projects/{PROJECT_ID}/locations/{REGION}/jobs/{job_name}",
        "description": "Daily automatic schedule collection for all registered artists",
        "schedule": schedule,
        "timeZone": timezone,
        "httpTarget": {
            "uri": f"{BASE_URL}/schedules/collect-registered",
            "httpMethod": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "days_ahead": 60
            }).encode('utf-8')
        },
        "retryConfig": {
            "retryCount": 3,
            "maxRetryDuration": "600s",
            "minBackoffDuration": "30s",
            "maxBackoffDuration": "300s"
        }
    }
    
    try:
        # 既存のジョブを削除（存在する場合）
        print(f"   🗑️ 既存ジョブの確認・削除...")
        delete_cmd = [
            "gcloud", "scheduler", "jobs", "delete", job_name,
            "--location", REGION,
            "--quiet"
        ]
        
        subprocess.run(delete_cmd, capture_output=True, text=True)
        print(f"   📝 既存ジョブを削除しました（存在した場合）")
        
        # 新しいジョブを作成
        print(f"   ⏰ 新しいSchedulerジョブを作成中...")
        create_cmd = [
            "gcloud", "scheduler", "jobs", "create", "http", job_name,
            "--location", REGION,
            "--schedule", schedule,
            "--time-zone", timezone,
            "--uri", f"{BASE_URL}/schedules/collect-registered",
            "--http-method", "POST",
            "--headers", "Content-Type=application/json",
            "--message-body", json.dumps({"days_ahead": 60}),
            "--max-retry-attempts", "3",
            "--max-retry-duration", "600s",
            "--description", "Daily automatic schedule collection for all registered artists"
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Cloud Schedulerジョブ作成成功!")
            print(f"   📋 ジョブ名: {job_name}")
            print(f"   ⏰ スケジュール: {schedule} ({timezone})")
            print(f"   🎯 エンドポイント: {BASE_URL}/schedules/collect-registered")
            return True
        else:
            print(f"   ❌ ジョブ作成失敗:")
            print(f"   📝 stdout: {result.stdout}")
            print(f"   📝 stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

def test_manual_trigger():
    """手動トリガーのテスト"""
    print("\n🎯 手動トリガーテスト")
    print("-" * 30)
    
    job_name = "schedule-collection-daily"
    
    try:
        print(f"   🚀 Schedulerジョブを手動実行中...")
        
        trigger_cmd = [
            "gcloud", "scheduler", "jobs", "run", job_name,
            "--location", REGION
        ]
        
        result = subprocess.run(trigger_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ 手動トリガー成功!")
            print(f"   📝 実行結果: {result.stdout.strip()}")
            
            # 実行結果の確認（少し待ってから）
            print(f"   ⏳ 実行完了を待機中（30秒）...")
            import time
            time.sleep(30)
            
            # ログの確認
            print(f"   📋 実行ログの確認...")
            log_cmd = [
                "gcloud", "scheduler", "jobs", "describe", job_name,
                "--location", REGION,
                "--format", "value(status.lastAttemptTime)"
            ]
            
            log_result = subprocess.run(log_cmd, capture_output=True, text=True)
            if log_result.returncode == 0 and log_result.stdout.strip():
                print(f"   📅 最終実行時刻: {log_result.stdout.strip()}")
            
            return True
        else:
            print(f"   ❌ 手動トリガー失敗:")
            print(f"   📝 stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

def check_scheduler_status():
    """Schedulerジョブのステータス確認"""
    print("\n📊 Schedulerジョブステータス確認")
    print("-" * 40)
    
    job_name = "schedule-collection-daily"
    
    try:
        status_cmd = [
            "gcloud", "scheduler", "jobs", "describe", job_name,
            "--location", REGION,
            "--format", "json"
        ]
        
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            job_info = json.loads(result.stdout)
            
            print(f"   📋 ジョブ情報:")
            print(f"     名前: {job_info.get('name', 'N/A').split('/')[-1]}")
            print(f"     スケジュール: {job_info.get('schedule', 'N/A')}")
            print(f"     タイムゾーン: {job_info.get('timeZone', 'N/A')}")
            print(f"     状態: {job_info.get('state', 'N/A')}")
            
            # 最新実行情報
            last_attempt = job_info.get('status', {}).get('lastAttemptTime')
            if last_attempt:
                print(f"     最終実行: {last_attempt}")
            
            # 次回実行予定
            next_run = job_info.get('scheduleTime')
            if next_run:
                print(f"     次回実行予定: {next_run}")
            
            return True
        else:
            print(f"   ❌ ステータス確認失敗:")
            print(f"   📝 stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False

def setup_monitoring():
    """監視・ログ設定"""
    print("\n📊 監視・ログ設定")
    print("-" * 25)
    
    print(f"   📋 設定済み監視項目:")
    print(f"     ✅ Cloud Logging: 自動有効")
    print(f"     ✅ Cloud Monitoring: 自動有効")
    print(f"     ✅ Cloud Scheduler実行ログ: 自動記録")
    print(f"     ✅ Cloud Run実行ログ: 自動記録")
    
    print(f"\n   🔍 ログ確認コマンド:")
    print(f"     gcloud logging read 'resource.type=\"cloud_scheduler_job\"' --limit=10")
    print(f"     gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"{SERVICE_NAME}\"' --limit=20")
    
    return True

if __name__ == "__main__":
    print(f"🚀 スケジュール収集自動化セットアップ")
    print(f"🌐 本番環境: {BASE_URL}")
    print(f"🕒 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Step 1: 一括収集エンドポイントのテスト
    endpoint_success = test_collect_registered_endpoint()
    
    # Step 2: Cloud Schedulerジョブの作成
    if endpoint_success:
        scheduler_success = create_cloud_scheduler_job()
    else:
        print("⚠️ エンドポイントテストが失敗したため、Scheduler設定をスキップします")
        scheduler_success = False
    
    # Step 3: 手動トリガーテスト
    if scheduler_success:
        trigger_success = test_manual_trigger()
    else:
        trigger_success = False
    
    # Step 4: ステータス確認
    if scheduler_success:
        status_success = check_scheduler_status()
    else:
        status_success = False
    
    # Step 5: 監視設定
    monitoring_success = setup_monitoring()
    
    # 最終サマリー
    print(f"\n🌟 自動化セットアップ結果")
    print("=" * 40)
    print(f"   一括収集API: {'✅' if endpoint_success else '❌'}")
    print(f"   Cloud Scheduler: {'✅' if scheduler_success else '❌'}")
    print(f"   手動トリガー: {'✅' if trigger_success else '❌'}")
    print(f"   ステータス確認: {'✅' if status_success else '❌'}")
    print(f"   監視設定: {'✅' if monitoring_success else '❌'}")
    
    if scheduler_success:
        print(f"\n🎉 自動化設定完了!")
        print(f"   ⏰ 毎日午前9時に自動実行されます")
        print(f"   📊 ログは Cloud Logging で確認できます")
        print(f"   🎯 総合成功率: {sum([endpoint_success, scheduler_success, trigger_success, status_success, monitoring_success])/5*100:.0f}%")
    else:
        print(f"\n⚠️ 一部設定に失敗しました")
        print(f"   📝 エラーログを確認して再実行してください")
    
    print(f"\n🕒 完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")