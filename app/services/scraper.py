# -*- coding: utf-8 -*-
"""
X (Twitter) 投稿取得モジュール
snscrapeを使用してアイドルの公式アカウントから最新投稿を取得
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import snscrape.modules.twitter as sntwitter
from app.config import get_message

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterScraper:
    """X (Twitter) スクレイピングクラス"""
    
    def __init__(self):
        self.max_tweets = 10  # 取得する最大投稿数
        self.days_back = 7    # 何日前まで遡るか
    
    def scrape_user_tweets(self, username: str, max_tweets: int = None) -> List[Dict[str, Any]]:
        """
        指定されたユーザーの最新投稿を取得
        
        Args:
            username: Xのユーザー名（@マークなし）
            max_tweets: 取得する最大投稿数
            
        Returns:
            投稿データのリスト
        """
        try:
            if max_tweets is None:
                max_tweets = self.max_tweets
            
            logger.info(f"@{username} の投稿を取得開始（最大{max_tweets}件）")
            
            # 日付範囲を設定（過去7日間）
            since_date = datetime.now() - timedelta(days=self.days_back)
            
            # snscrapeでツイートを取得
            tweets = []
            query = f"from:{username} since:{since_date.strftime('%Y-%m-%d')}"
            
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if i >= max_tweets:
                    break
                
                # 投稿データを構造化
                tweet_data = {
                    'id': tweet.id,
                    'url': tweet.url,
                    'date': tweet.date.isoformat(),
                    'content': tweet.rawContent,
                    'username': tweet.user.username,
                    'display_name': tweet.user.displayname,
                    'reply_count': tweet.replyCount,
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'hashtags': [tag for tag in tweet.hashtags] if tweet.hashtags else [],
                    'mentions': [mention.username for mention in tweet.mentionedUsers] if tweet.mentionedUsers else [],
                    'media': self._extract_media_info(tweet)
                }
                
                tweets.append(tweet_data)
                
            logger.info(f"@{username} の投稿を{len(tweets)}件取得完了")
            return tweets
            
        except Exception as e:
            logger.error(f"@{username} の投稿取得でエラー: {str(e)}")
            return []
    
    def _extract_media_info(self, tweet) -> List[Dict[str, str]]:
        """投稿のメディア情報を抽出"""
        media_info = []
        
        if hasattr(tweet, 'media') and tweet.media:
            for media in tweet.media:
                if hasattr(media, 'type') and hasattr(media, 'url'):
                    media_info.append({
                        'type': media.type,
                        'url': media.url
                    })
        
        return media_info
    
    def scrape_multiple_users(self, usernames: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数のユーザーの投稿を一括取得
        
        Args:
            usernames: ユーザー名のリスト
            
        Returns:
            ユーザー名をキーとした投稿データの辞書
        """
        all_tweets = {}
        
        for username in usernames:
            tweets = self.scrape_user_tweets(username)
            all_tweets[username] = tweets
            
        return all_tweets
    
    def save_tweets_to_json(self, tweets_data: Dict[str, List[Dict[str, Any]]], 
                           filename: str = None) -> str:
        """
        取得した投稿データをJSONファイルに保存
        
        Args:
            tweets_data: 投稿データ
            filename: 保存するファイル名
            
        Returns:
            保存されたファイル名
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tweets_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweets_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"投稿データを {filename} に保存完了")
            return filename
            
        except Exception as e:
            logger.error(f"ファイル保存エラー: {str(e)}")
            raise
    
    def filter_schedule_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        スケジュール関連の投稿をフィルタリング
        
        Args:
            tweets: 投稿データのリスト
            
        Returns:
            スケジュール関連の投稿のみ
        """
        schedule_keywords = [
            'スケジュール', 'イベント', 'コンサート', 'ライブ', 'LIVE', 'CONCERT',
            'リリース', 'RELEASE', 'MV', 'アルバム', 'シングル',
            'テレビ', 'TV', 'ラジオ', 'RADIO', '出演', '放送',
            '公演', 'ツアー', 'TOUR', 'ファンミーティング', 'ファンミ',
            '配信', 'STREAMING', 'オンライン',
            '月', '日', '時', '分', '開催', '開始', '開演'
        ]
        
        filtered_tweets = []
        
        for tweet in tweets:
            content = tweet.get('content', '').upper()
            
            # スケジュール関連キーワードが含まれているかチェック
            if any(keyword.upper() in content for keyword in schedule_keywords):
                filtered_tweets.append(tweet)
            
            # 日付パターンがあるかチェック
            elif self._contains_date_pattern(tweet.get('content', '')):
                filtered_tweets.append(tweet)
        
        logger.info(f"スケジュール関連投稿を{len(filtered_tweets)}件抽出")
        return filtered_tweets
    
    def _contains_date_pattern(self, text: str) -> bool:
        """テキストに日付パターンが含まれているかチェック"""
        import re
        
        date_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',  # 2024年1月15日
            r'\d{1,2}/\d{1,2}',            # 1/15
            r'\d{1,2}月\d{1,2}日',         # 1月15日
            r'\d{1,2}:\d{2}',              # 19:30
            r'\d{1,2}時\d{1,2}分?',        # 19時30分
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False

def get_idol_tweets(username: str, max_tweets: int = 10) -> List[Dict[str, Any]]:
    """
    アイドルの投稿を取得する便利関数
    
    Args:
        username: Xのユーザー名
        max_tweets: 取得する最大投稿数
        
    Returns:
        スケジュール関連の投稿データ
    """
    scraper = TwitterScraper()
    tweets = scraper.scrape_user_tweets(username, max_tweets)
    return scraper.filter_schedule_tweets(tweets)

def get_multiple_idols_tweets(usernames: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    複数のアイドルの投稿を一括取得する便利関数
    
    Args:
        usernames: ユーザー名のリスト
        
    Returns:
        ユーザー名をキーとしたスケジュール関連投稿の辞書
    """
    scraper = TwitterScraper()
    all_tweets = scraper.scrape_multiple_users(usernames)
    
    # 各ユーザーの投稿をスケジュール関連のみにフィルタリング
    filtered_tweets = {}
    for username, tweets in all_tweets.items():
        filtered_tweets[username] = scraper.filter_schedule_tweets(tweets)
    
    return filtered_tweets

# 使用例
if __name__ == "__main__":
    # テスト用のコード
    test_usernames = ['BTS_official', 'BLACKPINK']
    
    # 複数アイドルの投稿を取得
    tweets_data = get_multiple_idols_tweets(test_usernames)
    
    # JSONファイルに保存
    scraper = TwitterScraper()
    scraper.save_tweets_to_json(tweets_data)
    
    print("投稿取得とJSONファイル保存が完了しました")