# 日本語対応設定ガイド

## 概要
このプロジェクトは日本語での入力・出力を完全サポートしています。

## 設定済み項目

### 1. エンコーディング設定
- すべてのPythonファイル: UTF-8エンコーディング
- VS Code設定: 自動エンコーディング検出
- ターミナル環境: 日本語ロケール（ja_JP.UTF-8）

### 2. 日本語プロンプトテンプレート
- スケジュール抽出用の日本語プロンプト
- データ検証用の日本語メッセージ
- カレンダー説明文の日本語テンプレート

### 3. 日本語テキスト処理
- 全角・半角文字の正規化
- 日本語日付形式の自動抽出
- 日本語時刻表記の解析
- イベント種別の自動判定

## 使用方法

### 基本的な日本語入力例

```python
from src.config import get_message, get_prompt
from src.utils.japanese import JapaneseTextProcessor

# 日本語メッセージの取得
success_msg = get_message('success', 'schedule_added')
# -> "スケジュールが正常に追加されました"

# 日本語プロンプトの生成
prompt = get_prompt('schedule_extraction', text="BTS 1月15日 東京ドーム コンサート")

# 日本語テキストの処理
processor = JapaneseTextProcessor()
date = processor.extract_date_jp("2024年1月15日のコンサート")
# -> "2024-01-15"
```

### 日本語での操作例

1. **スケジュール登録**
   ```
   イベント名: BTS WORLD TOUR
   アーティスト名: BTS
   日付: 2024年1月15日
   時間: 18時30分
   場所: 東京ドーム
   ```

2. **検索クエリ**
   ```
   "BTS コンサート 東京"
   "NewJeans 新曲 リリース"
   "TWICE テレビ出演"
   ```

## トラブルシューティング

### 文字化け対策
- ファイル保存時は必ずUTF-8を使用
- ターミナルで`export LANG=ja_JP.UTF-8`を実行

### 日付認識の改善
日本語の日付表記は以下の形式に対応：
- 2024年1月15日
- 1月15日
- 1/15
- 01-15

### フォント設定
VS Codeで日本語表示を最適化：
```json
{
  "editor.fontFamily": "Source Han Code JP, Menlo, Monaco, monospace",
  "editor.fontSize": 14
}
```

## 推奨事項

1. **コメントとドキュメント**
   - コード内コメントは日本語で記述
   - 変数名は英語、説明は日本語を推奨

2. **ログメッセージ**
   - エラーメッセージは日本語で出力
   - デバッグ情報も日本語化

3. **ユーザーインターフェース**
   - すべてのUI要素を日本語化
   - 入力フォームのプレースホルダーも日本語

## 環境変数設定

プロジェクトルートに`.env`ファイルを作成：
```bash
LANG=ja_JP.UTF-8
LC_ALL=ja_JP.UTF-8
TZ=Asia/Tokyo
DEFAULT_LANGUAGE=ja
```