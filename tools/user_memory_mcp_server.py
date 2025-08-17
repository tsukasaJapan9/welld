import datetime
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process


class MemoryTag(Enum):
  """Predefined memory tag values (category-based)"""

  HOBBY = "hobby"
  PERSONAL_INFORMATION = "personal_information"
  PERSONALITY = "personality"
  HABIT = "habit"
  LEARNING = "learning"
  GOAL = "goal"
  PREFERENCE = "preference"
  INSTRUCTION_FOR_AI = "instruction_for_ai"


MEMORY_TAG_EXAMPLES = {
  MemoryTag.HOBBY: "books, music, movies, games, drawing, etc.",
  MemoryTag.PERSONAL_INFORMATION: "name, age, job, location, family, birth date, etc.",
  MemoryTag.PERSONALITY: "kind, optimistic, introverted, logical, etc.",
  MemoryTag.HABIT: "morning walk, daily meditation, journaling, exercising, etc.",
  MemoryTag.LEARNING: "Python, Spanish, machine learning, piano, etc.",
  MemoryTag.GOAL: "get fit, launch a startup, pass an exam, write a book, etc.",
  MemoryTag.PREFERENCE: "likes coffee, dislikes spicy food, prefers remote work, etc.",
  MemoryTag.INSTRUCTION_FOR_AI: "always respond briefly, use polite tone, ask clarifying questions, etc.",
}


class MemoryPriority(Enum):
  """Memory priority levels"""

  HIGH = "high"
  MID = "mid"
  LOW = "low"


class MemoryEntry(BaseModel):
  """メモリエントリの構造"""

  tags: List[str] = Field(..., description="タグのリスト")
  content: str = Field(..., description="メモリの内容")
  priority: str = Field(..., description="優先度 (high: 高, mid: 中, low: 低)")
  created_at: str = Field(..., description="作成日時")
  updated_at: str = Field(..., description="更新日時")
  reference_count: int = Field(default=0, description="参照された回数")


class MemorySearchResult(BaseModel):
  """メモリの検索結果"""

  content: str = Field(..., description="メモリの内容")
  tags: List[str] = Field(..., description="タグのリスト")
  priority: str = Field(..., description="優先度 (high: 高, mid: 中, low: 低)")
  created_at: str = Field(..., description="作成日時")
  updated_at: str = Field(..., description="更新日時")
  reference_count: int = Field(default=0, description="参照された回数")
  score: float = Field(..., description="類似度スコア")


class MemoryManager:
  """メモリの管理を行うクラス"""

  def __init__(self, memory_file: str = "user_memory.json"):
    self.memory_file = Path(memory_file)
    # メモリディレクトリを自動作成
    self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    self.memories: dict[str, MemoryEntry] = {}
    self._load_memories()

  def _load_memories(self):
    """メモリファイルからデータを読み込む"""
    if self.memory_file.exists():
      try:
        with open(self.memory_file, "r", encoding="utf-8") as f:
          data = json.load(f)
          for key, item in data.items():
            # 過去のデータにpriorityフィールドがない場合は"mid"をデフォルト値として設定
            if "priority" not in item:
              item["priority"] = "mid"
            # 過去のデータにreference_countフィールドがない場合は0をデフォルト値として設定
            if "reference_count" not in item:
              item["reference_count"] = 0
            # タグがENUMのリストにあるかチェック
            tmp_tags = []
            for tag in item["tags"]:
              if tag in [t.value for t in MemoryTag]:
                tmp_tags.append(tag)
            item["tags"] = tmp_tags if tmp_tags else [MemoryTag.PERSONALITY.value]

            try:
              self.memories[key] = MemoryEntry(**item)
            except Exception as e:
              print(f"Warning: Failed to load memory item: {e}, item: {item}")
              continue
      except (json.JSONDecodeError, KeyError):
        self.memories = {}
    else:
      self.memories = {}

  def _save_memories(self):
    """メモリをファイルに保存する"""
    self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    with open(self.memory_file, "w", encoding="utf-8") as f:
      json.dump(self.memories, f, ensure_ascii=False, indent=2)

  def add_memory(self, tags: List[str], content: str, priority: str) -> bool:
    """新しいメモリを追加"""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    memory = MemoryEntry(
      tags=tags,
      content=content,
      priority=priority,
      created_at=now,
      updated_at=now,
      reference_count=0,
    )
    self.memories[f"memory_{now}"] = memory
    self._save_memories()
    return True

  def update_memory(self, key: str, content: str) -> bool:
    """指定されたキーのメモリを更新"""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if key in self.memories.keys():
      self.memories[key].content = content
      self.memories[key].updated_at = now
      self._save_memories()
      return True
    return False

  def get_memory_by_key(self, key: str) -> Optional[MemoryEntry]:
    """指定されたキーのメモリを取得"""
    return self.memories.get(key)

  def search_memories(self, query: str, tag: Optional[str] = None) -> List[MemorySearchResult]:
    """メモリを検索"""
    results: List[MemorySearchResult] = []
    filtered_memories: dict[str, MemoryEntry] = {}

    # contentからMemoryを参照するための辞書
    # contentが重複している場合は最後のものが優先される

    # タグによるフィルタ
    if tag:
      filtered_memories = {key: memory for key, memory in self.memories.items() if tag in memory.tags}
    else:
      filtered_memories = self.memories.copy()

    # 類似度検索
    matched_memories = process.extract(
      query,
      {key: memory.content for key, memory in filtered_memories.items()},
      limit=5,
      scorer=fuzz.partial_ratio,
      score_cutoff=20,
    )

    for _, score, key in matched_memories:
      results.append(
        MemorySearchResult(
          tags=filtered_memories[key].tags,
          content=filtered_memories[key].content,
          priority=filtered_memories[key].priority,
          created_at=filtered_memories[key].created_at,
          updated_at=filtered_memories[key].updated_at,
          reference_count=filtered_memories[key].reference_count,
          score=score,
        )
      )
    return results

  def get_all_memories(self) -> List[MemorySearchResult]:
    """全てのメモリを取得"""
    return [
      MemorySearchResult(
        tags=memory.tags,
        content=memory.content,
        priority=memory.priority,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        reference_count=memory.reference_count,
        score=0,
      )
      for memory in self.memories.values()
    ]

  def delete_memory(self, key: str) -> bool:
    """指定されたキーのメモリを削除"""
    if key in self.memories:
      del self.memories[key]
      self._save_memories()
      return True
    return False


# 環境変数からメモリファイルの保存場所を取得
MEMORY_FILE = os.environ.get("MEMORY_FILE", "memory/user_memory.json")

# メモリマネージャーのインスタンス
memory_manager = MemoryManager(MEMORY_FILE)

# MCPサーバーの作成
mcp = FastMCP("user_memory_mcp_server", log_level="ERROR")


@mcp.tool("add_memory")
async def add_memory(tags: List[str], content: str, priority: str) -> Tuple[bool, str]:
  tag_list = ""
  for tag in MemoryTag:
    tag_list += f"- {tag.value}({MEMORY_TAG_EXAMPLES[tag]})\n"

  f"""
  Add a new memory with user's information.

  When to use:
      - When you want to record a new memory, experience, or observation
      - When creating the first entry for a specific event or moment
      - When you need to store user preferences, habits, or personal characteristics
      - When building a knowledge base of user behavior patterns
      - When you want to track progress or changes over time

  Args:
      tags (List[str]): List of tags.
      {tag_list}
      content (str): Memory content. Provide detailed description.
      priority (str): Priority level ("high", "mid", "low"). Must be specified.

  Returns:
      Tuple[bool, str]: Tuple containing operation result 
          - success (bool): Operation success/failure
          - message (str): Result message
  """
  try:
    # タグの検証
    valid_tags = [tag.value for tag in MemoryTag]
    invalid_tags = [tag for tag in tags if tag not in valid_tags]
    if invalid_tags:
      return False, f"Invalid tags: {invalid_tags}"

    # 優先度の検証
    valid_priorities = [priority.value for priority in MemoryPriority]
    if priority not in valid_priorities:
      return False, f"Invalid priority: {priority}"

    is_success = memory_manager.add_memory(tags, content, priority)
    return is_success, "Success to add memory"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("update_memory")
async def update_memory(key: str, content: str) -> Tuple[bool, str]:
  """
  Update a memory entry with the specified key.

  When to use:
      - When you need to modify existing memory content or tags
      - When updating progress or status of an ongoing activity
      - When correcting or refining previously recorded information
      - When adding new insights or observations to existing memories
      - When you want to change the categorization of a memory

  Args:
      key (str): Key of the memory to update. Must be in YYYYMMDDHHMMSS format.
                 Example: "memory_20240115103000"
      content (str): New memory content. Replaces existing content.

  Returns:
      Tuple[bool, str]: Tuple containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message

  """
  try:
    is_success = memory_manager.update_memory(key, content)
    if is_success:
      return True, "Success to update memory"
    else:
      return False, f"Error: {str(e)}"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("search_memories")
async def search_memories(query: str, tags: Optional[str] = None) -> List[MemorySearchResult]:
  tag_list = ""
  for tag in MemoryTag:
    tag_list += f"- {tag.value}({MEMORY_TAG_EXAMPLES[tag]})\n"

  """
  Search memories with flexible query and tag-based filtering.

  When to use:
      - When you want to find memories containing specific keywords or phrases
      - When you need to filter memories by specific categories or tags
      - When building search functionality for user interfaces
      - When you want to discover related memories across different time periods
      - When analyzing patterns or trends in user behavior and preferences
      - When you need to find memories that match multiple criteria

  Args:
      query (str): Search query. Specify text that appears in memory content or tags.
                   Example: "guitar" or "practice"
      tags (Optional[str]): Target tags for search. If specified, only memories with these tags are searched.
                                  {tag_list}

  Returns:
      List[MemorySearchResult]: List of search results
  """
  try:
    results = memory_manager.search_memories(query, tags)
    return results
  except Exception:
    return []


@mcp.tool("get_all_memories")
async def get_all_memories() -> List[MemorySearchResult]:
  """
  Retrieve all stored memory entries.

  When to use:
      - When you need to display a complete list of all memories
      - When building dashboards or overview pages
      - When you want to analyze all stored data for patterns or insights
      - When performing bulk operations on all memories
      - When you need to export or backup all memory data
      - When building administrative interfaces for memory management

  Args:
      None (no parameters required)

  Returns:
      List[MemorySearchResult]: List of all memories
  """
  try:
    memories = memory_manager.get_all_memories()
    return memories
  except Exception:
    return []


@mcp.tool("delete_memory")
async def delete_memory(key: str) -> Tuple[bool, str]:
  """
  Delete a memory entry with the specified key.

  When to use:
      - When you need to remove incorrect or outdated information
      - When cleaning up test data or temporary entries
      - When implementing user privacy controls (right to be forgotten)
      - When you want to remove memories that are no longer relevant
      - When managing storage space by removing old entries
      - When correcting data integrity issues

  Args:
      key (str): Key of the memory to delete. Must be in YYYYMMDDHHMMSS format.
                 Example: "20240115103000"

  Returns:
      Tuple[bool, str]: Tuple containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message

  """
  try:
    is_success = memory_manager.delete_memory(key)
    if is_success:
      return True, "Success to delete memory"
    else:
      return False, f"Error: {str(e)}"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("get_tag_list")
async def get_tag_list() -> List[str]:
  """
  Get the list of available tags.
  """
  return [tag.value for tag in MemoryTag]


@mcp.tool("get_priority_list")
async def get_priority_list() -> List[str]:
  """
  Get the list of available priorities.
  """
  return [priority.value for priority in MemoryPriority]


@mcp.tool("get_memory_stats")
async def get_memory_stats() -> dict[str, Any]:
  """
  Retrieve memory statistics. Provides analytical data including total count, key range, and tag usage frequency.

  When to use:
      - When you need to display dashboard metrics and analytics
      - When analyzing user behavior patterns and preferences
      - When building administrative or monitoring interfaces
      - When you want to understand which categories are most popular
      - When planning data management strategies
      - When generating reports or insights about memory usage
      - When monitoring system health and data distribution

  Args:
      None (no parameters required)

  Returns:
      dict: Dictionary containing statistics
        - total_memories (int): Total number of memories
        - key_range (dict): Range of keys
            - earliest (str): Oldest key (YYYYMMDDHHMMSS format)
            - latest (str): Newest key (YYYYMMDDHHMMSS format)
        - tag_counts (dict): Usage count for each tag
            - Key: Tag name (e.g., "趣味")
            - Value: Usage count
        - most_used_tags (List[tuple]): Top 5 most used tags
            - Each element: Tuple of (tag_name, usage_count)
  """
  try:
    memories = memory_manager.get_all_memories()

    # タグの統計
    tag_counts: dict[str, int] = {}
    for memory in memories:
      for tag in memory.tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # キー範囲
    keys = [memory.created_at for memory in memories]
    keys.sort()

    return {
      "total_memories": len(memories),
      "key_range": {"earliest": keys[0] if keys else None, "latest": keys[-1] if keys else None},
      "tag_counts": tag_counts,
      "most_used_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
    }
  except Exception:
    return {}


if __name__ == "__main__":
  memory_manager = MemoryManager(memory_file="/home/tsukasa/works/welld/memory/user_memory.json")

  # Test code
  import asyncio

  async def test():
    # Test adding memory
    result = await add_memory(["hobby", "learning"], "Started learning guitar", "high")
    print("Add memory:", result)

    # # Test searching memories
    # result = await search_memories("音楽")
    # print("Search memories:", result)
    # result = await get_memory_stats()
    # print("Get memory stats:", result)

  asyncio.run(test())

  # result = memory_manager.search_memories("音楽")
  # for r in result:
  #   print(r.model_dump_json())
  # result = memory_manager.search_memories("エージェント")
  # for r in result:
  #   print(r.model_dump_json())

  # mcp.run(transport="stdio")
