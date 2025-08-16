# Welld Frontend

This is the frontend application for Welld AI Agent.

## Getting Started

First, install the dependencies:

```bash
npm install
# or
yarn install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

Create a `.env.local` file in the frontend directory with the following content:

```bash
# APIサーバーのURL
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Features

- **Chat Interface**: AIエージェントとのチャット機能
- **Memory Statistics**: 蓄積されたメモリの統計情報表示
- **Responsive Design**: モバイルとデスクトップに対応したレスポンシブデザイン
- **Sidebar Navigation**: 折りたたみ可能なサイドバーナビゲーション

## API Integration

The frontend communicates with the Welld API server running on port 8000. Make sure the API server is running before using the frontend.

### Memory Statistics API

- **Endpoint**: `/api/memory/stats`
- **Method**: GET
- **Description**: メモリの統計情報を取得
- **Response**: 総メモリ数、タグ使用頻度、期間などの統計データ

## Development

### Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── api/            # API routes
│   │   └── memory/     # Memory-related APIs
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Home page
├── components/          # React components
│   ├── ChatInterface.tsx    # Chat interface
│   ├── Layout.tsx           # Layout wrapper
│   ├── MemoryStats.tsx      # Memory statistics
│   └── Sidebar.tsx          # Navigation sidebar
└── globals.css         # Global styles
```

### Key Components

- **ChatInterface**: AIエージェントとのチャット機能
- **MemoryStats**: メモリ統計の表示と管理
- **Sidebar**: ナビゲーションメニューとページ切り替え
- **Layout**: ページレイアウトの管理

## Dependencies

- **Next.js**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
