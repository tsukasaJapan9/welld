#!/usr/bin/env python3
"""
Simple AI Agent using Google ADK
ユーザーの入力に対して受け答えするシンプルなAIエージェント
"""

import asyncio
import json
import logging
import os
import random
import uuid
import warnings
from datetime import datetime, timedelta, timezone
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

from tools.user_memory_mcp_server import MemoryTag
from tools.utils.mcp_connect import MCPConnector

load_dotenv()


# 警告を無視
warnings.filterwarnings("ignore")

# ログレベルを設定
logging.basicConfig(level=logging.ERROR)

MODEL_NAME = "gemini-2.5-flash"
# MODEL_NAME = "gemini-2.5-pro"
APP_NAME = "SimpleAI"
USER_ID = "test_user"

# メモリファイルパス
USER_MEMORY_FILE = os.environ.get("USER_MEMORY_FILE", "memory/user_memory.json")

# スケジュールファイルパス
USER_SCHEDULE_FILE = os.environ.get("USER_SCHEDULE_FILE", "memory/user_schedule.json")


def before_model_modifier(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
  """Inspects/modifies the LLM request or skips the call."""
  # これでシステムプロンプトを見ることができる
  # print(llm_request.config.system_instruction)
  original_instruction = llm_request.config.system_instruction

  # 時刻情報を付け加える
  if original_instruction:
    current_time = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    new_instruction = f"{original_instruction}\n\n# 現在時刻\n{current_time}\n"
    llm_request.config.system_instruction = new_instruction

    # スケジュールを読み出してプロンプトに追加する
    with open(USER_SCHEDULE_FILE, "r", encoding="utf-8") as f:
      schedules = json.load(f)
    now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d")
    schedules = [schedule for schedule in schedules.values() if schedule["deadline"][:8] >= now]
    schedule_instruction = ""
    for schedule in schedules:
      schedule_instruction += f"{schedule['deadline']}: {schedule['content']}\n"
    
    # 記憶を読み出してプロンプトに追加する
    with open(USER_MEMORY_FILE, "r", encoding="utf-8") as f:
      memories = json.load(f)
    memories = [memory for memory in memories.values()]
    # パーソナルな情報を抽出
    personal_information = [memory for memory in memories if MemoryTag.PERSONAL_INFORMATION.value in memory["tags"]]
    # AIへの指示を抽出
    ai_instruction = [memory for memory in memories if MemoryTag.INSTRUCTION_FOR_AI.value in memory["tags"]]
    # その他の情報をランダムに抽出
    other_information = [
      memory
      for memory in memories
      if MemoryTag.PERSONAL_INFORMATION.value not in memory["tags"]
      and MemoryTag.INSTRUCTION_FOR_AI.value not in memory["tags"]
    ]
    other_information = random.sample(other_information, min(len(other_information), 10))
    memory_instruction = """
# ユーザの背景情報
以下はユーザに関する背景情報です。
毎回参照するとしつこいので会話の流れに合うときだけ参照してください。

## パーソナルな情報
{personal_information}

## AIへの指示
{ai_instruction}

## その他の情報
{other_information}

# スケジュール
{schedule_instruction}
"""
    personal_information_str = ""
    for memory in personal_information:
      print(memory)
      personal_information_str += f"{memory['tags']}: {memory['content']}\n"
    other_information_str = ""
    for memory in other_information:
      other_information_str += f"{memory['tags']}: {memory['content']}\n"
    ai_instruction_str = ""
    for memory in ai_instruction:
      ai_instruction_str += f"{memory['tags']}: {memory['content']}\n"

    llm_request.config.system_instruction = (
      llm_request.config.system_instruction
      + "\n"
      + memory_instruction.format(
        personal_information=personal_information_str,
        ai_instruction=ai_instruction_str,
        other_information=other_information_str,
        schedule_instruction=schedule_instruction,
      )
    )

    print(llm_request.config.system_instruction)

  return None


system_instruction = """
# あなたの役割
あなたは親切で役立つAIアシスタントです。
ユーザーの質問や要望に対して、丁寧で分かりやすい回答を提供してください。
またあなたはユーザとの会話を通してユーザに関する情報をメモリに蓄積し、それを検索することでユーザに
パーソナライズされたコミュニケーションを行います。
またユーザの背景情報も適宜参照してください。

# ルール
- 日本語で回答してください。

# メモリ使用ガイドライン
会話の連続性やコンテキスト保持を向上させるために、メモリツールを最大限に活用してください。

## メモリのタグ一覧
- **get_memory_tag_list**: メモリのタグ一覧を取得する。
- メモリを保存したり、更新する際はまずタグ一覧を取得して適切なタグを指定すること。

## メモリの優先度一覧
- **get_memory_priority_list**: メモリの優先度一覧を取得する。
- メモリを保存したり、更新する際はまず優先度一覧を取得して適切な優先度を指定すること。

## メモリを保存するためのツール
- **add_memory**: 重要な会話のやり取り、重要な意思決定、ユーザーの好みなど今後の会話で覚えておく価値のあるコンテキストを保存する。
- メモリを保存する際は、以下の手順で行うこと。
  - get_memory_tag_listを使ってタグ一覧を取得し適切なタグを選択
  - get_memory_priority_listを使って優先度一覧を取得し適切な優先度を選択
  - add_memoryを使ってメモリを保存する
- ユーザはパーソナライズされたコミュニケーションを望んでいるので、積極的にこのツールを使うこと。
- 具体的にはユーザの趣味、個人情報、性格、習慣、学習、目標、人間関係、趣向、あなたへの指示などです。
- 一時的な情報よりも、長期的に意味のある情報に焦点を当てること。

## メモリを検索するためのツール
- **search_memories**: 会話の開始時に過去ののメモリやコンテキストを検索する。
- ユーザーをより良く支援するために過去の背景情報が必要なときに使用する
- ユーザはパーソナライズされたコミュニケーションを望んでいるので、積極的にこのツールを使うこと。

## メモリを更新するためのツール
- **update_memory**: 過去のメモリに対して、新しい重要情報をと統合し、メモリの内容を再構築する。
- このツールを使う場合、まずはsearch_memoriesを使って関連メモリのkeyを取得し、そのkeyを使ってupdate_memoryを呼び出すこと。
- 進行中のプロジェクトや関係に意味のある進展があったときに更新する
- 関連情報を統合して、時間を通じて一貫したコンテキストを維持する

## メモリを削除するためのツール
- **delete_memory**: 不要なメモリを削除する。
- 背反する指示が含まれている場合、優先度が低いメモリを削除すること。
- しばらく参照されていない情報がある場合、メモリを削除すること。
- このツールを使う場合、まずはsearch_memoriesを使って関連メモリのkeyを取得し、そのkeyを使ってdelete_memoryを呼び出すこと。

これらのツールは、会話の連続性を構築し、よりパーソナライズされた支援を提供するために使用してください。
エラー防止や意図推測のための仕組みではありません。

# ユーザスケジュール管理ガイドライン
ユーザのスケジュールを把握し、適切なリマインド、フォローアップを行うために、スケジュールツールを最大限に活用してください。

## スケジュールの優先度一覧
- **get_schedule_priority_list**: スケジュールの優先度一覧を取得する。
- スケジュールを保存したり、更新する際はまず優先度一覧を取得して適切な優先度を指定すること。

## スケジュールを保存するためのツール
- **add_schedule**: ユーザの将来的なスケジュールを保存する。
- スケジュールを保存する際は、以下の手順で行うこと。
  - get_schedule_priority_listを使って優先度一覧を取得し適切な優先度を選択
  - add_scheduleを使ってスケジュールを保存する
- ユーザがスケジュールを忘れないようにあなたが適切にスケジュールを管理すること。

## スケジュールを検索するためのツール
- **search_schedules**: スケジュールを検索する。
- ユーザがスケジュールを忘れないようにこまめに検索してリマインドすること。
- ユーザに対してスケジュールのための準備などを促すこと。

## スケジュールを更新するためのツール
- **update_schedule**: 過去のスケジュールに対して、新しい重要情報をと統合し、スケジュールの内容を再構築する。
- このツールを使う場合、まずはsearch_schedulesを使って関連スケジュールのkeyを取得し、そのkeyを使ってupdate_scheduleを呼び出すこと。
- スケジュールの内容が変更になった場合はこのツールを使って更新すること。

## スケジュールを削除するためのツール
- **delete_schedule**: 不要なスケジュールを削除する。
- このツールを使う場合、まずはsearch_schedulesを使って関連スケジュールのkeyを取得し、そのkeyを使ってdelete_scheduleを呼び出すこと。
- 重複するスケジュールがある場合、優先度が低いスケジュールを削除すること。
- 一ヶ月以上前の予定は適宜削除すること。

これらのツールは、ユーザの予定のリマインド、及び予定の準備を促すことに使ってください。
"""

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
        instruction=system_instruction,
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
        print(
          f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}"
        )

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
      import traceback

      traceback.print_exc()
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
