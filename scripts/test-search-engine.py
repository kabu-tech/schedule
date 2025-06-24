#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
K-POP専用Custom Search Engineのテストスクリプト
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

def test_search_engine(api_key, search_engine_id, query):
    """Custom Search APIをテスト"""
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'num': 5,
        'hl': 'ja',
        'gl': 'jp'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n🔍 検索クエリ: {query}")
        print(f"📊 結果数: {len(data.get('items', []))}")
        print(f"🕒 検索時間: {data.get('searchInformation', {}).get('searchTime', 'N/A')}秒")
        
        for i, item in enumerate(data.get('items', [])[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   🔗 {item['link']}")
            print(f"   📝 {item['snippet'][:100]}...")
            
            # ドメインの信頼性チェック
            domain = item['link'].split('/')[2]
            reliability = check_domain_reliability(domain)
            print(f"   ⭐ 信頼度: {reliability}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API リクエストエラー: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON デコードエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def check_domain_reliability(domain):
    """ドメインの信頼性を評価"""
    high_reliability = [
        'smtown.com', 'ygfamily.com', 'jype.com', 'hybecorp.com',
        'weverse.io', 'natalie.mu', 'billboard-japan.com', 'barks.jp',
        'realsound.jp', 'soompi.com', 't.pia.jp', 'l-tike.com',
        'eplus.jp', 'ticketboard.jp', 'youtube.com'
    ]
    
    medium_reliability = [
        'oricon.co.jp', 'musicman.co.jp', 'spice.eplus.jp',
        'tower.jp', 'hmv.co.jp'
    ]
    
    low_reliability = [
        'blog', 'fc2.com', 'livedoor.jp', 'ameblo.jp',
        'wiki', 'forum', 'bbs'
    ]
    
    domain_lower = domain.lower()
    
    if any(reliable in domain_lower for reliable in high_reliability):
        return "🟢 高信頼"
    elif any(reliable in domain_lower for reliable in medium_reliability):
        return "🟡 中信頼"
    elif any(unreliable in domain_lower for unreliable in low_reliability):
        return "🔴 低信頼"
    else:
        return "⚪ 不明"

def main():
    """メイン関数"""
    print("=== K-POP Custom Search Engine テスト ===")
    
    # 環境変数の読み込み
    load_dotenv(override=True)
    
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("❌ 環境変数が設定されていません")
        print("   GOOGLE_API_KEY または GOOGLE_SEARCH_ENGINE_ID を確認してください")
        return
    
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🔍 Search Engine ID: {search_engine_id}")
    
    # テストクエリ
    test_queries = [
        "BLACKPINK コンサート 2025",
        "BTS ツアー 日程",
        "TWICE リリース 情報",
        "NewJeans テレビ出演",
        "aespa ファンミーティング"
    ]
    
    success_count = 0
    
    for query in test_queries:
        if test_search_engine(api_key, search_engine_id, query):
            success_count += 1
        print("\n" + "="*60)
    
    print(f"\n📊 テスト結果: {success_count}/{len(test_queries)} 成功")
    
    if success_count == len(test_queries):
        print("✅ 全てのテストが成功しました！")
    elif success_count > 0:
        print("⚠️ 部分的に成功しました")
    else:
        print("❌ 全てのテストが失敗しました")
        print("   Custom Search Engineの設定を確認してください")

if __name__ == "__main__":
    main()