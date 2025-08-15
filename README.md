# Welld AI Agent

Google ADK (Agent Development Kit) を使用したAIエージェントプロジェクトです。

## プロジェクト構成

```
welld/
├── agents/                    # AIエージェント（Python）
│   └── root_agent.py         # メインエージェント
├── frontend/                  # チャットUI（Next.js）
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/chat/     # チャットAPI
│   │   │   └── page.tsx      # メインページ
│   │   └── components/       # Reactコンポーネント
│   └── README.md             # フロントエンド詳細
├── pyproject.toml            # Python依存関係
├── uv.lock                   # Python依存関係ロック
└── README.md                 # このファイル
```

## 機能

### バックエンド（Python）
- 🤖 Google ADKを使用したAIエージェント
- 💬 Gemini 2.5 Flashモデルによる自然言語処理
- 🔄 セッション管理と会話履歴
- ⚡ 非同期処理による高速応答

### フロントエンド（Next.js）
- 🎨 モダンなチャットインターフェース
- 📱 レスポンシブデザイン
- 💬 リアルタイムメッセージ表示
- 🔌 APIエンドポイントによるバックエンド連携

## セットアップ

### 前提条件

- Python 3.13以上
- Node.js 18.0以上
- uv（Pythonパッケージマネージャー）

### バックエンドセットアップ

1. Python仮想環境を作成・アクティベート
```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows
```

2. 依存関係をインストール
```bash
uv sync
```

3. AIエージェントを実行
```bash
python agents/root_agent.py
```

### フロントエンドセットアップ

1. フロントエンドディレクトリに移動
```bash
cd frontend
```

2. 依存関係をインストール
```bash
npm install
```

3. 開発サーバーを起動
```bash
npm run dev
```

4. ブラウザで [http://localhost:3000](http://localhost:3000) を開く

## 使用方法

### バックエンド（CLI）
- ターミナルでAIエージェントと直接チャット
- 基本的な質問や会話が可能
- `quit` または `exit` で終了

### フロントエンド（Web UI）
- ブラウザでチャットインターフェースを使用
- 美しいUIでAIエージェントとチャット
- 現在はモック応答（後でバックエンドと接続予定）

## 技術スタック

### バックエンド
- **Python 3.13**: メイン言語
- **Google ADK**: AIエージェントフレームワーク
- **Gemini 2.5 Flash**: LLMモデル
- **uv**: パッケージマネージャー

### フロントエンド
- **Next.js 15.4**: Reactフレームワーク
- **TypeScript**: 型安全性
- **Tailwind CSS**: スタイリング
- **Lucide React**: アイコン

## 開発状況

### 完了済み
- ✅ Google ADK AIエージェントの基本実装
- ✅ セッション管理とセッションサービス
- ✅ Next.js 15.4フロントエンド
- ✅ チャットUIコンポーネント
- ✅ APIエンドポイント（モック）

### 進行中
- 🔄 フロントエンドとバックエンドの統合
- 🔄 実際のLLM応答の実装

### 今後の予定
- [ ] フロントエンドとバックエンドの完全統合
- [ ] リアルタイムチャット機能
- [ ] 会話履歴の永続化
- [ ] ユーザー認証システム
- [ ] ファイルアップロード機能

## トラブルシューティング

### よくある問題

1. **Python依存関係エラー**
   ```bash
   uv sync
   source .venv/bin/activate
   ```

2. **Node.js依存関係エラー**
   ```bash
   cd frontend
   npm install
   ```

3. **ポート競合**
   - フロントエンド: 3000番ポート
   - 必要に応じて `npm run dev -- -p 3001` でポート変更

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します！
