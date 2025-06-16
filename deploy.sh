#!/bin/bash
# K-POP Schedule Auto-Feed 手動デプロイスクリプト

set -e

# 設定
PROJECT_ID="your-project-id"
SERVICE_NAME="schedule-auto-feed"
REGION="asia-northeast1"
SOURCE_DIR="."

echo "🚀 K-POP Schedule Auto-Feed をデプロイ中..."

# Google Cloud プロジェクト設定
gcloud config set project $PROJECT_ID

# Cloud Run にデプロイ
gcloud run deploy $SERVICE_NAME \
  --source=$SOURCE_DIR \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=3600 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=10

echo "✅ デプロイ完了!"
echo "🌐 サービスURL: https://$SERVICE_NAME-$REGION.cloudfunctions.net"