#!/usr/bin/env python3
"""
Simple AI Agent using Google ADK
ユーザーの入力に対して受け答えするシンプルなAIエージェント
"""

import asyncio
import json
import logging
import os
import uuid
import warnings
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import agent_tool, google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.genai import types

from tools.utils.mcp_connect import MCPConnector

load_dotenv()


# 警告を無視
warnings.filterwarnings("ignore")

# ログレベルを設定
logging.basicConfig(level=logging.ERROR)

# MODEL_NAME = "gemini-2.5-flash"
MODEL_NAME = "gemini-2.5-pro"
APP_NAME = "SimpleAI"
USER_ID = "test_user"

# メモリファイルパス
USER_MEMORY_FILE = os.environ.get("USER_MEMORY_FILE", "memory/user_memory.json")


def before_model_modifier(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
  """Inspects/modifies the LLM request or skips the call."""
  # これでシステムプロンプトを見ることができる
  # print(llm_request.config.system_instruction)
  original_instruction = llm_request.config.system_instruction

  # 時刻情報を付け加える
  if original_instruction:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_instruction = f"{original_instruction}\n\n# 現在時刻\n{current_time}\n"
    llm_request.config.system_instruction = new_instruction

  # 記憶を読み出してプロンプトに追加する
  with open(USER_MEMORY_FILE, "r", encoding="utf-8") as f:
    memories = json.load(f)
  # high or midを抽出
  memories = [memory for memory in memories if memory["priority"] == "high" or memory["priority"] == "mid"]
  memory_instruction = "# メモリ\n以下はユーザに関するメモリ情報です。これらを適宜参照して回答してください。\n"
  for memory in memories:
    memory_instruction += f"{memory['tags']}: {memory['content']}\n"

  llm_request.config.system_instruction = llm_request.config.system_instruction + "\n" + memory_instruction

  print(llm_request.config.system_instruction)

  return None


search_agent = Agent(
  model="gemini-2.0-flash",
  name="SearchAgent",
  instruction="""
    You're a specialist in Google Search
    """,
  tools=[google_search],
)


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

    self.mcp_connector = MCPConnector()
    self.mcp_tools: list[MCPToolset] = []

  async def initialize(self, session_id: str, user_id: str):
    """
    エージェントの初期化処理
    ユーザが新しい一連の会話を始めたときにセッションなどを作成する
    """
    self.session_id = session_id
    self.user_id = user_id

    try:
      # MCPツール(stdio)を取得
      self.mcp_names, self.mcp_tools = self.mcp_connector.get_stdio_tools()
      self.mcp_tools.append(agent_tool.AgentTool(agent=search_agent))

      print("--------------------------------")
      print("Available MCP Tools:")
      for name in self.mcp_names:
        print(f"  - {name}")
      print("--------------------------------")

      # セッションサービスを作成
      self.session_service = InMemorySessionService()

      # セッションを作成
      self.session = await self.session_service.create_session(
        app_name=APP_NAME, user_id=self.user_id, session_id=self.session_id
      )

      # エージェントの作成
      self.agent = LlmAgent(
        name="SimpleAI",
        description="AIエージェントWelld",
        instruction="""
                # あなたの役割
                あなたは親切で役立つAIアシスタントです。
                ユーザーの質問や要望に対して、丁寧で分かりやすい回答を提供してください。

                # ルール
                - 日本語で回答してください。
              
                # 記憶について
                あなたは記憶モジュールを持っており、user_memory_mcp_serverというツールで実装されています。
                特にユーザの趣味趣向や性格、興味関心、習慣、健康、学習、人間関係、目標、感情、場所、時間に関する情報が得られた場合は
                必ずMCPのadd_memory関数を呼び出すことでメモリに保存してください。
                メモリに保存する際はユーザに承認を求める必要はありません。勝手に保存してください。
                そして積極的にメモリの情報を参照し、ユーザの趣向に合わせた回答をしてください。
                """,
        model=MODEL_NAME,
        tools=self.mcp_tools,
        before_model_callback=before_model_modifier,
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
