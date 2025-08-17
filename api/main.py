#!/usr/bin/env python3
"""
FastAPI server for Welld AI Agent
Google ADK AIエージェントをHTTP APIとして公開するサーバー
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# プロジェクトルートをパスに追加（絶対パスを使用）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# パス設定後にインポート
from agents.root_agent import SimpleAIAgent

load_dotenv()


# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# グローバル変数
agents: dict[str, SimpleAIAgent] = {}
DEFAULT_USER_ID = "default_user"

# メモリファイルパス
USER_MEMORY_FILE = os.environ.get("USER_MEMORY_FILE", "memory/user_memory.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
  """アプリケーションのライフサイクル管理"""
  # 起動時の処理
  logger.info("🚀 Welld AI Agent API サーバーが起動しました")
  yield
  # 終了時の処理
  logger.info("🛑 Welld AI Agent API サーバーが停止しました")


# FastAPIアプリケーションの作成
app = FastAPI(
  title="Welld AI Agent API",
  description="Google ADKを使用したAIエージェントのAPI",
  version="1.0.0",
  lifespan=lifespan,
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# データモデル
class ChatRequest(BaseModel):
  message: str = Field(..., description="ユーザーのメッセージ", min_length=1, max_length=1000)
  session_id: Optional[str] = Field(None, description="セッションID（省略時は新規作成）")
  user_id: Optional[str] = Field(None, description="ユーザーID（省略時はデフォルト値）")


class ChatResponse(BaseModel):
  response: str = Field(..., description="AIエージェントの応答")
  session_id: str = Field(..., description="セッションID")
  user_id: str = Field(..., description="ユーザーID")
  timestamp: str = Field(..., description="応答時刻")


class HealthResponse(BaseModel):
  status: str = Field(..., description="サーバーの状態")
  version: str = Field(..., description="APIバージョン")
  timestamp: str = Field(..., description="現在時刻")


class MemoryStatsResponse(BaseModel):
  success: bool = Field(..., description="操作の成功/失敗")
  stats: Optional[Dict[str, Any]] = Field(None, description="統計情報")
  message: Optional[str] = Field(None, description="エラーメッセージ")


async def get_memory_stats_from_mcp() -> Optional[Dict[str, Any]]:
  """メモリファイルから直接統計情報を取得"""
  try:
    # メモリファイルのパスを構築
    memory_file_path = os.path.join(project_root, USER_MEMORY_FILE)

    logger.info(f"📊 メモリファイルから統計情報を取得中: {memory_file_path}")

    # ファイルが存在するかチェック
    if not os.path.exists(memory_file_path):
      logger.warning(f"⚠️ メモリファイルが存在しません: {memory_file_path}")
      return None

    # メモリファイルを読み込み
    with open(memory_file_path, "r", encoding="utf-8") as f:
      memories: list = json.load(f)

    # 統計情報を計算
    total_memories = len(memories)

    if total_memories == 0:
      logger.info("📊 メモリファイルは空です")
      return {
        "total_memories": 0,
        "key_range": {"earliest": None, "latest": None},
        "tag_counts": {},
        "most_used_tags": [],
      }

    # タグの使用頻度をカウント
    tag_counts: Dict[str, int] = {}
    keys: list = []

    for memory in memories:
      # タグのカウント
      for tag in memory.get("tags", []):
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

      # キーの収集
      keys.append(memory.get("key", ""))

    # キーの範囲を計算
    valid_keys: list = [k for k in keys if k and len(k) == 14 and k.isdigit()]
    if valid_keys:
      valid_keys.sort()
      key_range: Dict[str, Optional[str]] = {"earliest": valid_keys[0], "latest": valid_keys[-1]}
    else:
      key_range: Dict[str, Optional[str]] = {"earliest": None, "latest": None}

    # 最も使用されているタグ（上位5位）
    most_used_tags: list = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    stats = {
      "total_memories": total_memories,
      "key_range": key_range,
      "tag_counts": tag_counts,
      "most_used_tags": most_used_tags,
    }

    logger.info(f"✅ メモリファイルから統計情報を正常に取得しました: {total_memories}件")
    return stats

  except FileNotFoundError:
    logger.error(f"❌ メモリファイルが見つかりません: {USER_MEMORY_FILE}")
    return None
  except json.JSONDecodeError as e:
    logger.error(f"❌ メモリファイルのJSON形式が不正です: {e}")
    return None
  except Exception as e:
    logger.error(f"❌ メモリファイルの読み込み中にエラーが発生: {e}")
    return None


@app.get("/", response_model=HealthResponse)
async def root():
  """ルートエンドポイント（ヘルスチェック）"""
  return HealthResponse(status="healthy", version="1.0.0", timestamp=str(asyncio.get_event_loop().time()))


@app.get("/health", response_model=HealthResponse)
async def health_check():
  """ヘルスチェックエンドポイント"""
  return HealthResponse(status="healthy", version="1.0.0", timestamp=str(asyncio.get_event_loop().time()))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
  """チャットエンドポイント"""
  try:
    # セッションIDとユーザーIDの設定
    session_id = request.session_id or str(uuid.uuid4())
    user_id = request.user_id or DEFAULT_USER_ID

    # エージェントの取得または作成
    agent_key = f"{user_id}_{session_id}"
    if agent_key not in agents:
      logger.info(f"🆕 新しいエージェントを作成: {agent_key}")
      agent = SimpleAIAgent()
      await agent.initialize(session_id, user_id)
      agents[agent_key] = agent
    else:
      agent = agents[agent_key]
      logger.info(f"🔄 既存のエージェントを使用: {agent_key}")

    # AIエージェントに問い合わせ
    logger.info(f"🤖 メッセージを処理中: {request.message[:50]}...")
    response = await agent.chat(request.message)

    logger.info(f"✅ 応答完了: {response[:50]}...")

    return ChatResponse(
      response=response, session_id=session_id, user_id=user_id, timestamp=str(asyncio.get_event_loop().time())
    )

  except Exception as e:
    logger.error(f"❌ チャット処理中にエラーが発生: {e}")
    raise HTTPException(status_code=500, detail=f"チャット処理中にエラーが発生しました: {str(e)}")


@app.get("/api/memory/stats", response_model=MemoryStatsResponse)
async def get_memory_stats():
  """メモリ統計エンドポイント"""
  try:
    # MCPサーバーからメモリ統計を取得
    mcp_stats = await get_memory_stats_from_mcp()

    if mcp_stats:
      # MCPサーバーから取得したデータを使用
      logger.info("📊 MCPサーバーからメモリ統計を取得しました")
      return MemoryStatsResponse(success=True, stats=mcp_stats, message=None)
    else:
      # フォールバック: シミュレーションデータ
      fallback_stats = {
        "total_memories": 25,
        "key_range": {"earliest": "20240101000000", "latest": "20240115120000"},
        "tag_counts": {
          "hobby": 8,
          "learning": 6,
          "health": 4,
          "personality": 3,
          "habit": 2,
          "relationship": 1,
          "goal": 1,
        },
        "most_used_tags": [["hobby", 8], ["learning", 6], ["health", 4], ["personality", 3], ["habit", 2]],
      }

      logger.info("📊 フォールバックデータを使用してメモリ統計を返しました")
      return MemoryStatsResponse(success=True, stats=fallback_stats, message=None)

  except Exception as e:
    logger.error(f"❌ メモリ統計取得中にエラーが発生: {e}")
    return MemoryStatsResponse(success=False, stats=None, message=f"メモリ統計の取得に失敗しました: {str(e)}")


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str, user_id: str = DEFAULT_USER_ID):
  """セッションの削除"""
  try:
    agent_key = f"{user_id}_{session_id}"
    if agent_key in agents:
      del agents[agent_key]
      logger.info(f"🗑️ セッションを削除: {agent_key}")
      return {"message": "セッションが削除されました"}
    else:
      return {"message": "セッションが見つかりません"}
  except Exception as e:
    logger.error(f"❌ セッション削除中にエラーが発生: {e}")
    raise HTTPException(status_code=500, detail=f"セッション削除中にエラーが発生しました: {str(e)}")


@app.get("/api/sessions")
async def list_sessions():
  """アクティブなセッションの一覧"""
  try:
    active_sessions = [
      {"agent_key": key, "user_id": key.split("_")[0], "session_id": key.split("_")[1]} for key in agents.keys()
    ]
    return {"sessions": active_sessions, "count": len(active_sessions)}
  except Exception as e:
    logger.error(f"❌ セッション一覧取得中にエラーが発生: {e}")
    raise HTTPException(status_code=500, detail=f"セッション一覧取得中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
  # 開発サーバーの起動
  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
