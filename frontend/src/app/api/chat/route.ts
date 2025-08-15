import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { error: 'メッセージが必要です' },
        { status: 400 }
      );
    }

    // TODO: 実際のAIエージェントと接続
    // 現在はモック応答を返す
    await new Promise(resolve => setTimeout(resolve, 1000));

    const mockResponse = `「${message}」についてのご質問ですね。現在はモック応答ですが、後で実際のAIエージェントと接続予定です。

このAPIエンドポイントは、バックエンドのGoogle ADK AIエージェントと接続するように設計されています。`;

    return NextResponse.json({
      response: mockResponse,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: '内部サーバーエラーが発生しました' },
      { status: 500 }
    );
  }
}
