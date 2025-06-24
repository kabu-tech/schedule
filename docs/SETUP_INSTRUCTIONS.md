# 🎯 K-POP専用Custom Search Engine設定手順

## 📋 今すぐ実行する手順

### Step 1: 新しい検索エンジンを作成

1. **ブラウザで以下URLにアクセス**
   ```
   https://programmablesearchengine.google.com/controlpanel/all
   ```

2. **「新しい検索エンジンを追加」をクリック**

3. **基本情報を入力**
   - **検索エンジン名**: `K-POP Schedule Search Engine`
   - **説明**: `K-POPアーティストのスケジュール情報専用検索エンジン`

### Step 2: 検索対象の設定

**「検索対象」セクションで以下を入力：**

#### 🟢 含めるサイト (Sites to include)
```
smtown.com
ygfamily.com  
jype.com
hybecorp.com
weverse.io
natalie.mu/music
billboard-japan.com
barks.jp
realsound.jp
soompi.com
allkpop.com
t.pia.jp
l-tike.com
eplus.jp
ticketboard.jp
youtube.com
oricon.co.jp
```

#### 🔴 除外するサイト (Sites to exclude)
```
*.blog.*
*.fc2.com
*.livedoor.jp  
*.ameblo.jp
*wiki*
*forum*
*bbs*
```

### Step 3: 詳細設定

1. **言語設定**
   - 言語: 日本語
   - 国/地域: 日本

2. **検索設定**
   - 安全検索: 中程度
   - 画像検索: 有効

3. **「作成」をクリック**

### Step 4: 検索エンジンIDを取得

1. **作成された検索エンジンをクリック**
2. **「概要」タブの「基本」セクション**
3. **「検索エンジンID」をコピー**

### Step 5: 環境変数を更新

**`.env`ファイルを編集：**
```bash
# 新しい検索エンジンIDに置き換え
GOOGLE_SEARCH_ENGINE_ID=新しい検索エンジンID
```

### Step 6: テスト実行

```bash
# 検索エンジンのテスト
python scripts/test-search-engine.py
```

## 🎯 設定完了後の確認項目

### ✅ チェックリスト
- [ ] 新しい検索エンジンが作成された
- [ ] K-POP関連サイトが含まれている
- [ ] 不適切なサイトが除外されている  
- [ ] 検索エンジンIDが取得された
- [ ] `.env`ファイルが更新された
- [ ] テストスクリプトで結果が取得できる

### 🔍 期待される結果
テスト実行後、以下のような結果が得られるはずです：
- BLACKPINK関連: 公式サイト、チケット情報、メディア記事
- BTS関連: HYBE公式、音楽ナタリー、チケットサイト
- 信頼度: 🟢高信頼 のサイトが上位表示

## 🚀 次のステップ

設定完了後：
1. **実際のスケジュール収集テスト**
2. **Gemini抽出精度の検証**
3. **信頼性フィルタリングの調整**

---

**⚠️ 重要: この設定作業は手動で行う必要があります。**
**設定完了後、Claudeにお知らせください。**