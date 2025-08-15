# Welld AI Chat Frontend

Next.js 15.4を使用したシンプルなチャットUIです。

## 機能

- 🤖 モダンなチャットインターフェース
- 💬 リアルタイムメッセージ表示
- 🎨 Tailwind CSSによる美しいデザイン
- 📱 レスポンシブデザイン
- ⚡ Next.js 15.4の最新機能

## セットアップ

### 前提条件

- Node.js 18.0以上
- npm または yarn

### インストール

1. 依存関係をインストール
```bash
npm install
```

2. 開発サーバーを起動
```bash
npm run dev
```

3. ブラウザで [http://localhost:3000](http://localhost:3000) を開く

## 使用方法

1. チャットインターフェースが表示されます
2. 入力フィールドにメッセージを入力
3. 送信ボタンをクリックまたはEnterキーを押す
4. AIアシスタントからの応答を確認

## プロジェクト構造

```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts    # チャットAPIエンドポイント
│   │   ├── globals.css         # グローバルスタイル
│   │   ├── layout.tsx          # レイアウト
│   │   └── page.tsx            # メインページ
│   └── components/
│       └── ChatInterface.tsx   # チャットUIコンポーネント
├── public/                     # 静的ファイル
├── package.json               # 依存関係
└── README.md                  # このファイル
```

## 技術スタック

- **Next.js 15.4**: Reactフレームワーク
- **TypeScript**: 型安全性
- **Tailwind CSS**: ユーティリティファーストCSS
- **Lucide React**: 美しいアイコン
- **ESLint**: コード品質

## 開発

### 利用可能なスクリプト

```bash
npm run dev          # 開発サーバー起動
npm run build        # プロダクションビルド
npm run start        # プロダクションサーバー起動
npm run lint         # ESLint実行
```

### カスタマイズ

- `src/components/ChatInterface.tsx` でチャットUIをカスタマイズ
- `src/app/api/chat/route.ts` でAPIエンドポイントをカスタマイズ
- `tailwind.config.js` でTailwind CSSをカスタマイズ

## 今後の改善予定

- [ ] 実際のAIエージェントとの接続
- [ ] 会話履歴の保存
- [ ] ユーザー認証
- [ ] リアルタイム更新
- [ ] ファイルアップロード
- [ ] 音声入力

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
