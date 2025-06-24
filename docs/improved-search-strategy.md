# 🎯 改良版検索戦略：拡張可能なアプローチ

## 問題分析
- 検索段階での制限 → ジャンル拡張性の欠如
- 固定サイトリスト → 新しい情報源の見逃し
- K-POP特化 → 汎用性の損失

## 🚀 Solution 1: Universal Search + AI信頼性判定

### アプローチ
1. **汎用検索エンジン**を使用（サイト制限なし）
2. **Gemini AI**で信頼性とジャンル適合性を同時判定
3. **動的フィルタリング**でより精密な制御

### 実装方法
```python
# 汎用検索 → AI判定のパイプライン
search_results = google_search(query)  # 制限なし
filtered_results = gemini_reliability_filter(search_results, genre="K-POP")
schedule_events = gemini_extract_schedules(filtered_results)
```

### メリット
- ✅ あらゆるジャンルに対応可能
- ✅ 新しい情報源を自動発見
- ✅ 信頼性判定の精度向上
- ✅ メンテナンス不要

## 🚀 Solution 2: 段階的フィルタリング戦略

### Phase 1: 広範囲検索
```python
# 制限なしで検索
results = google_search(f"{artist_name} schedule 2025")
```

### Phase 2: AI信頼性スコアリング
```python
prompt = f"""
以下の検索結果を評価してください：

【評価基準】
1. 信頼性 (0.0-1.0)
   - 公式サイト: 0.9-1.0
   - 大手メディア: 0.7-0.9
   - チケットサイト: 0.8-0.9
   - 個人ブログ: 0.1-0.3
   - 噂サイト: 0.0-0.2

2. 関連性 (0.0-1.0)
   - {genre}に直接関連: 0.8-1.0
   - 部分的に関連: 0.4-0.7
   - 関連性なし: 0.0-0.3

【検索結果】
{search_results}

【出力形式】
{{
  "filtered_results": [
    {{
      "url": "...",
      "title": "...", 
      "snippet": "...",
      "reliability_score": 0.85,
      "relevance_score": 0.92,
      "reasoning": "公式サイトで正確な日程情報"
    }}
  ]
}}

信頼性0.6未満は除外してください。
"""
```

### Phase 3: 動的閾値調整
```python
# ジャンルごとに閾値を調整
thresholds = {
    "K-POP": {"reliability": 0.7, "relevance": 0.8},
    "J-POP": {"reliability": 0.7, "relevance": 0.8},
    "Classical": {"reliability": 0.8, "relevance": 0.7},
    "Theater": {"reliability": 0.6, "relevance": 0.9}
}
```

## 🚀 Solution 3: ハイブリッド戦略

### 実装アイデア
1. **第1段階**: 汎用検索で幅広く収集
2. **第2段階**: ドメイン信頼性DB + AI判定
3. **第3段階**: ユーザーフィードバック学習

### ドメイン信頼性データベース
```python
DOMAIN_RELIABILITY = {
    # エンターテイメント系
    "smtown.com": 0.95,
    "ygfamily.com": 0.95,
    "natalie.mu": 0.90,
    "oricon.co.jp": 0.85,
    
    # チケット系  
    "eplus.jp": 0.90,
    "pia.jp": 0.90,
    
    # メディア系
    "nikkei.com": 0.85,
    "asahi.com": 0.85,
    
    # 要注意
    "*.blog.*": 0.2,
    "*.fc2.com": 0.1
}
```

## 🎯 推奨実装順序

### Step 1: 汎用検索エンジンに変更
- 現在の制限ありCustom Search → 制限なしに変更
- または、Google Search API直接利用

### Step 2: AI信頼性判定プロンプト強化
```python
UNIVERSAL_RELIABILITY_PROMPT = """
以下の検索結果から、{genre}の{query}に関する
信頼性の高い情報のみを抽出してください。

【汎用信頼性基準】
- 公式サイト・機関サイト
- 確立されたメディア・ニュースサイト  
- 公式チケットサービス
- 認証済みSNSアカウント

【除外対象】
- 個人ブログ・まとめサイト
- 憶測・噂・未確認情報
- 広告サイト・アフィリエイトサイト

ジャンル適合性も同時に評価してください。
"""
```

### Step 3: 段階的テスト
1. K-POPで精度確認
2. J-POP、アニメ等で拡張性確認
3. クラシック、演劇等で汎用性確認

## 🚀 長期的な改善案

### Learning System
- ユーザーフィードバックによる信頼性学習
- 新しいドメインの自動信頼性評価
- ジャンル別最適化の自動調整

### Multi-Source Integration
- 複数検索エンジンの併用
- SNS API連携（公式アカウント）
- RSS/API直接取得

この方式なら、K-POP以外への拡張も容易で、
より高精度な情報収集が可能になります。