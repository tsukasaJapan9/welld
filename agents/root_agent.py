#!/usr/bin/env python3
"""
Simple AI Agent using Google ADK
ユーザーの入力に対して受け答えするシンプルなAIエージェント
"""

import asyncio

from google.adk import Agent
from google.adk.models import Gemini


class SimpleAIAgent:
    """シンプルなAIエージェントクラス"""

    def __init__(self):
        """エージェントの初期化"""
        self.agent = None

    async def initialize(self):
        """エージェントの初期化処理"""
        try:
            # Geminiモデルを設定
            model = Gemini()

            # エージェントの作成
            self.agent = Agent(
                name="SimpleAI",
                description="シンプルなAIエージェント",
                instruction="""
                あなたは親切で役立つAIアシスタントです。
                ユーザーの質問や要望に対して、丁寧で分かりやすい回答を提供してください。
                日本語で回答してください。
                """,
                model=model,
            )
            print("✅ AIエージェントが初期化されました")
            print(f"📝 使用モデル: {model.model}")

        except Exception as e:
            print(f"❌ エージェントの初期化に失敗しました: {e}")
            raise

    async def chat(self, user_input: str) -> str:
        """ユーザーの入力に対して応答を生成"""
        if not self.agent:
            return "エージェントが初期化されていません"

        try:
            # Google ADKのrun_asyncメソッドを使って応答を生成
            # 現在は基本的な応答を返す（実際のLLM応答は後で実装）

            # 基本的な応答パターン（フォールバック用）
            basic_responses = {
                "こんにちは": "こんにちは！何かお手伝いできることはありますか？",
                "hello": "Hello! How can I help you today?",
                "天気": "申し訳ございませんが、現在の天気情報を取得する機能は実装されていません。",
                "時間": "現在時刻を確認する機能は実装されていませんが、基本的な質問にはお答えできます。",
                "名前": "私はSimpleAIという名前のAIアシスタントです。よろしくお願いします！",
            }

            # 基本的な応答パターンをチェック
            for pattern, response in basic_responses.items():
                if pattern in user_input:
                    return response

            # その他の質問には、より一般的な応答を返す
            return f"「{user_input}」についてのご質問ですね。現在は基本的な応答のみ可能ですが、より詳細な機能を追加予定です。"

        except Exception as e:
            return f"エラーが発生しました: {e}"

    async def interactive_chat(self):
        """インタラクティブなチャットセッションを開始"""
        print("🤖 AIエージェントとのチャットを開始します")
        print("終了するには 'quit' または 'exit' と入力してください")
        print("基本的な質問例: こんにちは、天気、時間、名前")
        print("-" * 50)

        while True:
            try:
                # ユーザー入力を受け取り
                user_input = input("👤 あなた: ").strip()

                # 終了条件をチェック
                if user_input.lower() in ["quit", "exit", "終了", "さようなら"]:
                    print("👋 チャットを終了します。お疲れ様でした！")
                    break

                if not user_input:
                    continue

                # AIエージェントの応答を取得
                print("🤖 AI: 考え中...")
                response = await self.chat(user_input)
                print(f"🤖 AI: {response}")
                print("-" * 50)

            except KeyboardInterrupt:
                print("\n👋 チャットを終了します。お疲れ様でした！")
                break
            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")


async def main():
    """メイン関数"""
    agent = SimpleAIAgent()

    try:
        # エージェントを初期化
        await agent.initialize()

        # インタラクティブチャットを開始
        await agent.interactive_chat()

    except Exception as e:
        print(f"❌ プログラムの実行中にエラーが発生しました: {e}")


if __name__ == "__main__":
    # 非同期メイン関数を実行
    asyncio.run(main())
