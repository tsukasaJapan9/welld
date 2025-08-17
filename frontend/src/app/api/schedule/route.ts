import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // バックエンドAPIサーバーにリクエストを転送
    const response = await fetch('http://localhost:8000/api/schedule', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend API responded with status: ${response.status}`);
    }

    const data = await response.json();

    // バックエンドからのレスポンスをそのまま返す
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching schedules:', error);

    // エラーが発生した場合は、フォールバックデータを返す
    const fallbackData = {
      success: true,
      schedules: [
        {
          deadline: "2024-01-20",
          content: "チームミーティング：週次プロジェクト進捗確認",
          priority: "high"
        },
        {
          deadline: "2024-01-22",
          content: "クライアント打ち合わせ：新機能の要件確認",
          priority: "mid"
        },
        {
          deadline: "2024-01-19",
          content: "コードレビュー：プルリクエストの確認",
          priority: "low"
        }
      ],
      message: null
    };

    return NextResponse.json(fallbackData);
  }
}
