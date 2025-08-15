# Welld AI Agent API Server

FastAPIを使用したAIエージェントのHTTP APIサーバーです。

## 機能

- 🤖 Google ADK AIエージェントとのHTTP通信
- 💬 チャットエンドポイント
- 🔄 セッション管理
- 🌐 CORS対応（フロントエンド連携）
- 📊 自動APIドキュメント生成

## セットアップ

### 前提条件

- Python 3.13以上
- 仮想環境が有効化されていること
- FastAPI、uvicornがインストールされていること

### 起動方法

1. 仮想環境を有効化
```bash
source ../.venv/bin/activate
```

2. APIサーバーを起動
```bash
python main.py
```

3. ブラウザでアクセス
- APIサーバー: [http://localhost:8000](http://localhost:8000)
- APIドキュメント: [http://localhost:8000/docs](http://localhost:8000/docs)
- ヘルスチェック: [http://localhost:8000/health](http://localhost:8000/health)

## API エンドポイント

### ヘルスチェック

#### GET /
サーバーの状態を確認

**レスポンス例:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "1234567890.123"
}
```

### チャット

#### POST /api/chat
AIエージェントとチャット

**リクエスト例:**
```json
{
  "message": "こんにちは",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**レスポンス例:**
```json
{
  "response": "こんにちは！何かお手伝いできることはありますか？",
  "session_id": "generated-session-id",
  "user_id": "default_user",
  "timestamp": "1234567890.123"
}
```

### セッション管理

#### GET /api/sessions
アクティブなセッションの一覧を取得

#### DELETE /api/session/{session_id}
指定されたセッションを削除

## 使用方法

### 基本的なチャット

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは"}'
```

### セッションを指定したチャット

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "続きの質問です",
    "session_id": "existing-session-id"
  }'
```

### セッションの削除

```bash
curl -X DELETE "http://localhost:8000/api/session/existing-session-id"
```

## アーキテクチャ

### コンポーネント

- **FastAPI**: Webフレームワーク
- **SimpleAIAgent**: Google ADK AIエージェント
- **セッション管理**: ユーザーごとのエージェントインスタンス管理
- **CORS**: フロントエンドからのアクセス許可

### データフロー

1. フロントエンドからメッセージを受信
2. セッションIDに基づいてエージェントを取得/作成
3. AIエージェントにメッセージを送信
4. 応答をフロントエンドに返却

## 開発

### ログレベル

- INFO: 一般的な操作ログ
- ERROR: エラー情報
- DEBUG: デバッグ情報（必要に応じて設定）

### 設定

- ポート: 8000
- ホスト: 0.0.0.0（全インターフェース）
- リロード: 有効（開発モード）

## トラブルシューティング

### よくある問題

1. **ポート競合**
   - 8000番ポートが使用中の場合は、`main.py`でポート番号を変更

2. **依存関係エラー**
   - 仮想環境が有効化されているか確認
   - `pip install fastapi uvicorn`を実行

3. **CORSエラー**
   - フロントエンドのURLが`allow_origins`に含まれているか確認

## 今後の改善予定

- [ ] 認証・認可システム
- [ ] レート制限
- [ ] ログの永続化
- [ ] メトリクス収集
- [ ] ヘルスチェックの詳細化
- [ ] セッションの永続化
