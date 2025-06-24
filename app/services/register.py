# -*- coding: utf-8 -*-
"""
アーティスト登録サービス
ユーザーが推しアーティストを登録・管理するための機能
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ArtistRegisterService:
    """アーティスト登録管理サービス"""
    
    # K-POPアーティストのサンプルリスト（自動補完用）
    SUGGESTED_ARTISTS = [
        "BTS", "SEVENTEEN", "Stray Kids", "ENHYPEN", "TXT",
        "NCT", "NCT DREAM", "NCT 127", "WayV", "ATEEZ",
        "THE BOYZ", "TREASURE", "&TEAM", "RIIZE", "ZEROBASEONE",
        "BLACKPINK", "TWICE", "NewJeans", "LE SSERAFIM", "IVE",
        "aespa", "ITZY", "NMIXX", "Kep1er", "STAYC",
        "(G)I-DLE", "EVERGLOW", "LOONA", "fromis_9", "VIVIZ"
    ]
    
    def __init__(self, firestore_client=None):
        """
        初期化
        
        Args:
            firestore_client: Firestoreクライアント
        """
        self.firestore_client = firestore_client
        # メモリ内ストレージ（Firestoreが利用できない場合のフォールバック）
        self._temp_storage: Dict[str, List[Dict[str, Any]]] = {}
        
        # Firestoreクライアントの利用可能性をチェック
        self.use_firestore = firestore_client is not None
        
        if self.use_firestore:
            logger.info("ArtistRegisterService initialized with Firestore backend")
        else:
            logger.warning("ArtistRegisterService initialized with memory-only backend")
    
    def register_artist(self, user_id: str, artist_name: str, 
                       notification_enabled: bool = True) -> Dict[str, Any]:
        """
        アーティストを登録
        
        Args:
            user_id: ユーザーID
            artist_name: アーティスト名
            notification_enabled: 通知を有効にするか
            
        Returns:
            登録結果
        """
        # アーティスト名の正規化
        normalized_name = self._normalize_artist_name(artist_name)
        
        # バリデーション
        if not normalized_name:
            raise ValueError("アーティスト名を入力してください")
        
        # 既存の登録をチェック
        if self.use_firestore:
            try:
                # Firestoreで効率的にチェック
                if self.firestore_client.check_artist_exists(user_id, normalized_name):
                    raise ValueError(f"{normalized_name}は既に登録されています")
            except Exception as e:
                logger.error(f"Failed to check artist existence in Firestore: {e}")
                # フォールバック: 全件取得でチェック
                existing_artists = self.get_user_artists(user_id)
                if any(artist['name'] == normalized_name for artist in existing_artists):
                    raise ValueError(f"{normalized_name}は既に登録されています")
        else:
            # メモリ内ストレージでチェック
            existing_artists = self.get_user_artists(user_id)
            if any(artist['name'] == normalized_name for artist in existing_artists):
                raise ValueError(f"{normalized_name}は既に登録されています")
        
        # 新規登録データ
        artist_data = {
            'id': self._generate_artist_id(user_id, normalized_name),
            'name': normalized_name,
            'original_name': artist_name,
            'notification_enabled': notification_enabled,
            'registered_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        # 保存処理（Firestore使用可能な場合はFirestore、そうでなければメモリ内ストレージ）
        if self.use_firestore:
            try:
                # Firestoreに保存
                doc_id = self.firestore_client.save_user_artist(user_id, artist_data)
                logger.info(f"Artist registered to Firestore: {normalized_name} for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to save to Firestore, falling back to memory: {e}")
                # フォールバック: メモリ内ストレージに保存
                if user_id not in self._temp_storage:
                    self._temp_storage[user_id] = []
                self._temp_storage[user_id].append(artist_data)
        else:
            # メモリ内ストレージに保存
            if user_id not in self._temp_storage:
                self._temp_storage[user_id] = []
            self._temp_storage[user_id].append(artist_data)
            logger.info(f"Artist registered to memory: {normalized_name} for user {user_id}")
        
        return {
            'success': True,
            'artist': artist_data,
            'message': f'{normalized_name}を登録しました'
        }
    
    def unregister_artist(self, user_id: str, artist_id: str) -> Dict[str, Any]:
        """
        アーティストの登録を解除
        
        Args:
            user_id: ユーザーID
            artist_id: アーティストID
            
        Returns:
            削除結果
        """
        if self.use_firestore:
            try:
                # Firestoreから削除
                success = self.firestore_client.delete_user_artist(user_id, artist_id)
                if success:
                    logger.info(f"Artist unregistered from Firestore: {artist_id} for user {user_id}")
                    return {
                        'success': True,
                        'message': 'アーティストの登録を解除しました'
                    }
                else:
                    raise ValueError("指定されたアーティストが見つかりません")
            except Exception as e:
                logger.error(f"Failed to delete from Firestore: {e}")
                raise ValueError("アーティストの削除に失敗しました")
        else:
            # メモリ内ストレージから削除
            if user_id not in self._temp_storage:
                raise ValueError("登録されたアーティストがありません")
            
            # 削除対象を検索
            artists = self._temp_storage[user_id]
            original_count = len(artists)
            
            # フィルタリングで削除
            self._temp_storage[user_id] = [
                artist for artist in artists if artist['id'] != artist_id
            ]
            
            if len(self._temp_storage[user_id]) == original_count:
                raise ValueError("指定されたアーティストが見つかりません")
            
            logger.info(f"Artist unregistered from memory: {artist_id} for user {user_id}")
            return {
                'success': True,
                'message': 'アーティストの登録を解除しました'
            }
    
    def get_user_artists(self, user_id: str) -> List[Dict[str, Any]]:
        """
        ユーザーの登録アーティスト一覧を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            アーティストリスト
        """
        if self.use_firestore:
            try:
                # Firestoreから取得
                artists = self.firestore_client.get_user_artists(user_id)
                logger.debug(f"Retrieved {len(artists)} artists from Firestore for user {user_id}")
                return artists
            except Exception as e:
                logger.error(f"Failed to get artists from Firestore, falling back to memory: {e}")
                # フォールバック: メモリ内ストレージから取得
                return self._temp_storage.get(user_id, [])
        else:
            # メモリ内ストレージから取得
            return self._temp_storage.get(user_id, [])
    
    def update_notification_setting(self, user_id: str, artist_id: str, 
                                  enabled: bool) -> Dict[str, Any]:
        """
        通知設定を更新
        
        Args:
            user_id: ユーザーID
            artist_id: アーティストID
            enabled: 通知を有効にするか
            
        Returns:
            更新結果
        """
        if self.use_firestore:
            try:
                # Firestoreで更新
                update_data = {
                    'notification_enabled': enabled
                }
                success = self.firestore_client.update_user_artist(user_id, artist_id, update_data)
                if success:
                    logger.info(f"Notification setting updated in Firestore: {artist_id} = {enabled}")
                    return {
                        'success': True,
                        'message': f'通知設定を{"有効" if enabled else "無効"}にしました'
                    }
                else:
                    raise ValueError("指定されたアーティストが見つかりません")
            except Exception as e:
                logger.error(f"Failed to update notification in Firestore: {e}")
                raise ValueError("通知設定の更新に失敗しました")
        else:
            # メモリ内ストレージで更新
            artists = self.get_user_artists(user_id)
            
            for artist in artists:
                if artist['id'] == artist_id:
                    artist['notification_enabled'] = enabled
                    artist['last_updated'] = datetime.now().isoformat()
                    
                    logger.info(f"Notification setting updated in memory: {artist_id} = {enabled}")
                    return {
                        'success': True,
                        'message': f'通知設定を{"有効" if enabled else "無効"}にしました'
                    }
            
            raise ValueError("指定されたアーティストが見つかりません")
    
    def search_artists(self, query: str) -> List[str]:
        """
        アーティスト名の検索（自動補完用）
        
        Args:
            query: 検索クエリ
            
        Returns:
            マッチするアーティスト名のリスト
        """
        if not query:
            return []
        
        query_lower = query.lower()
        matches = []
        
        for artist in self.SUGGESTED_ARTISTS:
            if query_lower in artist.lower():
                matches.append(artist)
        
        # 部分一致を優先度順にソート
        matches.sort(key=lambda x: (
            not x.lower().startswith(query_lower),  # 前方一致を優先
            x.lower().index(query_lower),  # より前の位置でマッチを優先
            len(x)  # 短い名前を優先
        ))
        
        return matches[:10]  # 上位10件を返す
    
    def _normalize_artist_name(self, name: str) -> str:
        """
        アーティスト名を正規化
        
        Args:
            name: 元のアーティスト名
            
        Returns:
            正規化されたアーティスト名
        """
        # 前後の空白を削除
        name = name.strip()
        
        # 連続する空白を1つに
        name = re.sub(r'\s+', ' ', name)
        
        # 全角英数字を半角に変換
        name = name.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        ))
        
        return name
    
    def _generate_artist_id(self, user_id: str, artist_name: str) -> str:
        """
        アーティストIDを生成
        
        Args:
            user_id: ユーザーID
            artist_name: アーティスト名
            
        Returns:
            生成されたID
        """
        # シンプルなID生成（後で改善可能）
        import hashlib
        data = f"{user_id}:{artist_name}:{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def get_all_registered_artists(self) -> List[str]:
        """
        全ユーザーの登録アーティスト名を重複なしで取得
        （スケジュール検索で使用）
        
        Returns:
            アーティスト名のリスト
        """
        if self.use_firestore:
            try:
                # Firestoreから取得
                artists = self.firestore_client.get_all_registered_artists()
                logger.debug(f"Retrieved {len(artists)} unique artists from Firestore")
                return artists
            except Exception as e:
                logger.error(f"Failed to get all artists from Firestore, falling back to memory: {e}")
                # フォールバック: メモリ内ストレージから取得
                all_artists = set()
                for user_artists in self._temp_storage.values():
                    for artist in user_artists:
                        all_artists.add(artist['name'])
                return sorted(list(all_artists))
        else:
            # メモリ内ストレージから取得
            all_artists = set()
            for user_artists in self._temp_storage.values():
                for artist in user_artists:
                    all_artists.add(artist['name'])
            return sorted(list(all_artists))