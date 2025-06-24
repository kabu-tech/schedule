# -*- coding: utf-8 -*-
"""
Firestore データベースクライアント
アーティスト登録情報の永続化
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Firestoreデータベースクライアント"""
    
    def __init__(self):
        """
        初期化
        環境変数からFirestore設定を取得
        """
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'kpop-sched-dev')
        self.collection_name = os.getenv('FIRESTORE_COLLECTION', 'user_artists')
        
        # Firestoreクライアントの初期化
        try:
            self.db = firestore.Client(project=self.project_id)
            logger.info(f"Firestore client initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
        
        # コレクションの参照
        self.collection = self.db.collection(self.collection_name)
    
    def save_user_artist(self, user_id: str, artist_data: Dict[str, Any]) -> str:
        """
        ユーザーのアーティスト情報を保存
        
        Args:
            user_id: ユーザーID
            artist_data: アーティスト情報
            
        Returns:
            作成されたドキュメントID
        """
        try:
            # ドキュメントデータの準備
            doc_data = {
                'user_id': user_id,
                'artist_id': artist_data['id'],
                'name': artist_data['name'],
                'original_name': artist_data['original_name'],
                'notification_enabled': artist_data['notification_enabled'],
                'registered_at': artist_data['registered_at'],
                'last_updated': artist_data['last_updated'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # ドキュメントIDの生成（user_id + artist_id の組み合わせ）
            doc_id = f"{user_id}_{artist_data['id']}"
            
            # Firestoreに保存
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(doc_data)
            
            logger.info(f"Artist saved to Firestore: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to save artist to Firestore: {e}")
            raise
    
    def get_user_artists(self, user_id: str) -> List[Dict[str, Any]]:
        """
        ユーザーの登録アーティスト一覧を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            アーティスト情報のリスト
        """
        try:
            # ユーザーIDでフィルタリングして取得（order_byを削除してインデックス要件を回避）
            query = self.collection.where(
                filter=FieldFilter("user_id", "==", user_id)
            )
            
            docs = query.stream()
            
            artists = []
            for doc in docs:
                data = doc.to_dict()
                # 元の形式に変換
                artist_data = {
                    'id': data.get('artist_id'),
                    'name': data.get('name'),
                    'original_name': data.get('original_name'),
                    'notification_enabled': data.get('notification_enabled', True),
                    'registered_at': data.get('registered_at'),
                    'last_updated': data.get('last_updated')
                }
                artists.append(artist_data)
            
            logger.info(f"Retrieved {len(artists)} artists for user {user_id}")
            return artists
            
        except Exception as e:
            logger.error(f"Failed to get user artists from Firestore: {e}")
            raise
    
    def delete_user_artist(self, user_id: str, artist_id: str) -> bool:
        """
        ユーザーのアーティスト登録を削除
        
        Args:
            user_id: ユーザーID
            artist_id: アーティストID
            
        Returns:
            削除成功の場合True
        """
        try:
            doc_id = f"{user_id}_{artist_id}"
            doc_ref = self.collection.document(doc_id)
            
            # ドキュメントの存在確認
            doc = doc_ref.get()
            if not doc.exists:
                logger.warning(f"Document not found for deletion: {doc_id}")
                return False
            
            # 削除実行
            doc_ref.delete()
            logger.info(f"Artist deleted from Firestore: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete artist from Firestore: {e}")
            raise
    
    def update_user_artist(self, user_id: str, artist_id: str, 
                          update_data: Dict[str, Any]) -> bool:
        """
        ユーザーのアーティスト情報を更新
        
        Args:
            user_id: ユーザーID
            artist_id: アーティストID
            update_data: 更新データ
            
        Returns:
            更新成功の場合True
        """
        try:
            doc_id = f"{user_id}_{artist_id}"
            doc_ref = self.collection.document(doc_id)
            
            # ドキュメントの存在確認
            doc = doc_ref.get()
            if not doc.exists:
                logger.warning(f"Document not found for update: {doc_id}")
                return False
            
            # 更新データに更新時刻を追加
            update_data['updated_at'] = datetime.now().isoformat()
            update_data['last_updated'] = datetime.now().isoformat()
            
            # 更新実行
            doc_ref.update(update_data)
            logger.info(f"Artist updated in Firestore: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update artist in Firestore: {e}")
            raise
    
    def get_all_registered_artists(self) -> List[str]:
        """
        全ユーザーの登録アーティスト名を重複なしで取得
        （スケジュール検索で使用）
        
        Returns:
            アーティスト名のリスト
        """
        try:
            docs = self.collection.stream()
            
            artist_names = set()
            for doc in docs:
                data = doc.to_dict()
                if 'name' in data:
                    artist_names.add(data['name'])
            
            result = sorted(list(artist_names))
            logger.info(f"Retrieved {len(result)} unique artist names")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all registered artists: {e}")
            raise
    
    def check_artist_exists(self, user_id: str, artist_name: str) -> bool:
        """
        指定されたアーティストが既に登録されているかチェック
        
        Args:
            user_id: ユーザーID
            artist_name: アーティスト名
            
        Returns:
            既に登録されている場合True
        """
        try:
            query = (self.collection
                    .where(filter=FieldFilter("user_id", "==", user_id))
                    .where(filter=FieldFilter("name", "==", artist_name)))
            
            docs = list(query.stream())
            exists = len(docs) > 0
            
            logger.debug(f"Artist exists check for {user_id}/{artist_name}: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check artist existence: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Firestore接続の健全性チェック
        
        Returns:
            ヘルスチェック結果
        """
        try:
            # 簡単なクエリでFirestore接続をテスト
            test_query = self.collection.limit(1)
            list(test_query.stream())
            
            return {
                'status': 'healthy',
                'project_id': self.project_id,
                'collection': self.collection_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Firestore health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }