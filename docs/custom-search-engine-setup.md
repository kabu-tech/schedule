# K-POP専用Custom Search Engine設定手順

## 前提条件
- Googleアカウントが必要
- Google Cloud Projectが設定済み

## Step 1: 新しい検索エンジンの作成

1. **Programmable Search Engineコンソール**にアクセス
   - URL: https://programmablesearchengine.google.com/controlpanel/all

2. **新しい検索エンジンを追加**
   - 「新しい検索エンジンを追加」をクリック

3. **基本設定**
   - **名前**: `K-POP Schedule Search Engine`
   - **検索対象**: 下記の信頼できるサイトを追加

## Step 2: 検索対象サイトの設定

### 含めるサイト (Include)
```
smtown.com/*
ygfamily.com/*
jype.com/*
hybecorp.com/*
weverse.io/*
natalie.mu/music/*
billboard-japan.com/*
barks.jp/*
realsound.jp/*
soompi.com/*
t.pia.jp/*
l-tike.com/*
eplus.jp/*
ticketboard.jp/*
youtube.com/*
```

### 除外するサイト (Exclude)
```
*.blog.*
*.fc2.com/*
*.livedoor.jp/*
*.ameblo.jp/*
*wiki*
*forum*
*bbs*
*掲示板*
```

## Step 3: 検索設定の調整

### 基本設定
- **言語**: 日本語
- **国/地域**: 日本
- **安全検索**: 中程度

### 高度な設定
- **画像検索**: 有効
- **音声検索**: 無効
- **検索候補**: 有効

## Step 4: 検索エンジンIDの取得

1. **概要**タブで検索エンジンIDをコピー
2. `.env`ファイルに設定
   ```bash
   GOOGLE_SEARCH_ENGINE_ID=新しい検索エンジンID
   ```

## Step 5: テスト実行

### 手動テスト
1. 検索エンジンのテストページで動作確認
2. 以下のクエリでテスト：
   - `BLACKPINK コンサート 2025`
   - `BTS ツアー 日程`
   - `TWICE リリース 情報`

### API テスト
```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=NEW_SEARCH_ENGINE_ID&q=BLACKPINK+schedule+2025"
```

## Step 6: 品質改善

### 検索結果の評価項目
- ✅ 公式情報が上位に表示される
- ✅ 正確な日程情報が含まれる
- ✅ 信頼できるソースからの情報
- ❌ 個人ブログや噂サイトが除外される

### 調整が必要な場合
1. サイトリストの見直し
2. 除外キーワードの追加
3. 検索パラメータの調整

## 注意事項

### 制限事項
- 1日あたり100クエリまで無料
- それ以上は$5/1000クエリ

### セキュリティ
- APIキーの適切な管理
- 不正利用の防止
- レート制限の実装

### モニタリング
- 検索結果の品質定期チェック
- 新しい信頼できるサイトの追加
- 不適切なサイトの除外