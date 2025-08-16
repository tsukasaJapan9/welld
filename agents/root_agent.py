#!/usr/bin/env python3
"""
Simple AI Agent using Google ADK
ユーザーの入力に対して受け答えするシンプルなAIエージェント
"""

import asyncio
import logging
import uuid
import warnings

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()


# 警告を無視
warnings.filterwarnings("ignore")

# ログレベルを設定
logging.basicConfig(level=logging.ERROR)

MODEL_NAME = "gemini-2.5-flash"
APP_NAME = "SimpleAI"
USER_ID = "test_user"


class SimpleAIAgent:
  """シンプルなAIエージェントクラス"""

  def __init__(self):
    """エージェントの初期化"""
    self.agent = None
    self.runner = None
    self.session_service = None
    self.session = None
    self.session_id: str | None = None
    self.user_id: str | None = None

  async def initialize(self, session_id: str, user_id: str):
    """
    エージェントの初期化処理
    ユーザが新しい一連の会話を始めたときにセッションなどを作成する
    """
    self.session_id = session_id
    self.user_id = user_id

    try:
      # セッションサービスを作成
      self.session_service = InMemorySessionService()

      # セッションを作成
      self.session = await self.session_service.create_session(
        app_name=APP_NAME, user_id=self.user_id, session_id=self.session_id
      )

      # エージェントの作成
      self.agent = Agent(
        name="SimpleAI",
        description="シンプルなAIエージェント",
        instruction="""
                あなたは親切で役立つAIアシスタントです。
                ユーザーの質問や要望に対して、丁寧で分かりやすい回答を提供してください。
                日本語で回答してください。
                """,
        model=MODEL_NAME,
      )

      # ランナーを作成
      self.runner = Runner(
        agent=self.agent,
        app_name=APP_NAME,
        session_service=self.session_service,
      )

      print("✅ AIエージェントが初期化されました")
      print(f"📝 使用モデル: {MODEL_NAME}")
      print(f"🆔 セッションID: {self.session_id}")
      print("🔄 セッションサービスとランナーが設定されました")

    except Exception as e:
      print(f"❌ エージェントの初期化に失敗しました: {e}")
      raise

  async def call_agent_async(self, query: str) -> str:
    """Sends a query to the agent and prints the final response."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text: str = "Agent did not produce a final response."

    try:
      # user_idとsession_idが設定されていることを確認
      if self.user_id is None or self.session_id is None:
        return "ユーザーIDまたはセッションIDが設定されていません"

      # runnerが設定されていることを確認
      if self.runner is None:
        return "ランナーが設定されていません"

      async for event in self.runner.run_async(user_id=self.user_id, session_id=self.session_id, new_message=content):
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        if event.is_final_response():
          if event.content and event.content.parts:
            text_part = event.content.parts[0].text
            if text_part is not None:
              final_response_text = text_part
          elif event.actions and event.actions.escalate:  # Handle potential errors/escalations
            final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"

          # Add more checks here if needed (e.g., specific error codes)
          # Stop processing events once the final response is found
          break

    except Exception as e:
      print(f"⚠️ エージェント実行中にエラーが発生しました: {e}")
      final_response_text = f"エラーが発生しました: {e}"

    return final_response_text

  async def chat(self, user_input: str) -> str:
    """ユーザーの入力に対して応答を生成"""
    if not self.agent or not self.runner:
      return "エージェントが初期化されていません"

    try:
      # Google ADKのRunnerを使って実際のLLM応答を生成
      print("🤖 LLMに問い合わせ中...")

      if self.user_id is None or self.session_id is None:
        raise ValueError("ユーザーIDまたはセッションIDが設定されていません")

      final_response_text = await self.call_agent_async(user_input)

      return final_response_text

    except Exception as e:
      print(f"⚠️ LLM応答生成中にエラーが発生しました: {e}")
      return "エラーが発生しました"

  async def interactive_chat(self):
    """インタラクティブなチャットセッションを開始"""
    print("🤖 AIエージェントとのチャットを開始します")
    print("終了するには 'quit' または 'exit' と入力してください")
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
    session_id = str(uuid.uuid4())
    user_id = "test_user"
    await agent.initialize(session_id, user_id)

    # インタラクティブチャットを開始
    await agent.interactive_chat()

  except Exception as e:
    print(f"❌ プログラムの実行中にエラーが発生しました: {e}")


if __name__ == "__main__":
  # 非同期メイン関数を実行
  asyncio.run(main())
