import datetime
import json
import os
from enum import Enum
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field


class MemoryTag(Enum):
  """Predefined memory tag values (category-based)"""

  # Main categories
  HOBBY = "hobby"
  PERSONALITY = "personality"
  HABIT = "habit"
  HEALTH = "health"
  LEARNING = "learning"
  RELATIONSHIP = "relationship"
  GOAL = "goal"
  EMOTION = "emotion"
  LOCATION = "location"
  TIME = "time"
  PREFERENCE = "preference"


class MemoryPriority(Enum):
  """Memory priority levels"""

  HIGH = "high"
  MID = "mid"
  LOW = "low"


class MemoryEntry(BaseModel):
  """メモリエントリの構造"""

  key: str = Field(..., description="メモリのキー (YYYYMMDDHHMMSS形式)")
  tags: List[str] = Field(..., description="タグのリスト")
  content: str = Field(..., description="メモリの内容")
  priority: str = Field(..., description="優先度 (high: 高, mid: 中, low: 低)")
  created_at: str = Field(..., description="作成日時")
  updated_at: str = Field(..., description="更新日時")


class MemorySearchResult(BaseModel):
  """メモリ検索結果の構造"""

  key: str = Field(..., description="メモリのキー")
  tags: List[str] = Field(..., description="タグ")
  content: str = Field(..., description="内容")
  priority: str = Field(..., description="優先度 (high: 高, mid: 中, low: 低)")
  relevance_score: float = Field(..., description="関連性スコア")


class MemoryManager:
  """メモリの管理を行うクラス"""

  def __init__(self, memory_file: str = "user_memory.json"):
    self.memory_file = Path(memory_file)
    # メモリディレクトリを自動作成
    self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    self.memories: List[MemoryEntry] = []
    self._load_memories()

  def _load_memories(self):
    """メモリファイルからデータを読み込む"""
    if self.memory_file.exists():
      try:
        with open(self.memory_file, "r", encoding="utf-8") as f:
          data = json.load(f)
          self.memories = []
          for item in data:
            # 過去のデータにpriorityフィールドがない場合は"mid"をデフォルト値として設定
            if "priority" not in item:
              item["priority"] = "mid"
            try:
              self.memories.append(MemoryEntry(**item))
            except Exception as e:
              print(f"Warning: Failed to load memory item: {e}, item: {item}")
              continue
      except (json.JSONDecodeError, KeyError):
        self.memories = []
    else:
      self.memories = []

  def _save_memories(self):
    """メモリをファイルに保存する"""
    self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    with open(self.memory_file, "w", encoding="utf-8") as f:
      json.dump([memory.model_dump() for memory in self.memories], f, ensure_ascii=False, indent=2)

  def add_memory(self, key: str, tags: List[str], content: str, priority: str) -> MemoryEntry:
    """新しいメモリを追加"""
    now = datetime.datetime.now().isoformat()
    memory = MemoryEntry(key=key, tags=tags, content=content, priority=priority, created_at=now, updated_at=now)
    self.memories.append(memory)
    self._save_memories()
    return memory

  def update_memory(
    self, key: str, tags: List[str], content: str, priority: Optional[str] = None
  ) -> Optional[MemoryEntry]:
    """指定されたキーのメモリを更新"""
    now = datetime.datetime.now().isoformat()
    for memory in self.memories:
      if memory.key == key:
        memory.tags = tags
        memory.content = content
        if priority is not None:
          memory.priority = priority
        memory.updated_at = now
        self._save_memories()
        return memory
    return None

  def get_memory_by_key(self, key: str) -> Optional[MemoryEntry]:
    """指定されたキーのメモリを取得"""
    for memory in self.memories:
      if memory.key == key:
        return memory
    return None

  def search_memories(self, query: str, tags: Optional[List[str]] = None) -> List[MemorySearchResult]:
    """メモリを検索"""
    results = []

    for memory in self.memories:
      relevance_score = 0.0

      # タグによる検索
      if tags:
        tag_matches = sum(1 for tag in tags if tag in memory.tags)
        if tag_matches > 0:
          relevance_score += tag_matches * 0.5

      # 内容による検索
      if query.lower() in memory.content.lower():
        relevance_score += 1.0

      # タグによる検索
      for tag in memory.tags:
        if query.lower() in tag.lower():
          relevance_score += 0.8

      if relevance_score > 0:
        results.append(
          MemorySearchResult(
            key=memory.key,
            tags=memory.tags,
            content=memory.content,
            priority=memory.priority,
            relevance_score=relevance_score,
          )
        )

    # 関連性スコアでソート
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results

  def get_all_memories(self) -> List[MemoryEntry]:
    """全てのメモリを取得"""
    return self.memories

  def delete_memory(self, key: str) -> bool:
    """指定されたキーのメモリを削除"""
    for i, memory in enumerate(self.memories):
      if memory.key == key:
        del self.memories[i]
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
async def add_memory(key: str, tags: List[str], content: str, priority: str) -> dict:
  """
  Add a new memory entry.

  When to use:
      - When you want to record a new memory, experience, or observation
      - When creating the first entry for a specific event or moment
      - When you need to store user preferences, habits, or personal characteristics
      - When building a knowledge base of user behavior patterns
      - When you want to track progress or changes over time

  Args:
      key (str): Memory key in YYYYMMDDHHMMSS format.
                 Example: "20240115103000" (January 15, 2024, 10:30:00)
      tags (List[str]): List of tags. Only predefined tags are allowed.
                        Example: ["hobby", "learning"] or ["health", "habit", "preference"]
      content (str): Memory content. Provide detailed description.
      priority (str): Priority level ("high", "mid", "low"). Must be specified.

  Returns:
      dict: Dictionary containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message
          - memory (dict): Information of added memory (on success)

  Raises:
      ValueError: When key format is invalid
      Exception: When other errors occur

  Example:
      >>> result = await add_memory(
      ...     key="20240115103000",
      ...     tags=["hobby", "learning"],
      ...     content="Started learning guitar. The chord positions are difficult but fun."
      ... )
      >>> print(result)
      {'success': True, 'message': 'Memory added successfully', 'memory': {...}}

  Note:
      - If a memory with the same key already exists, it will be overwritten
      - Tags must be selected from the 10 predefined categories
      - Key must be exactly 14 digits
  """
  try:
    # キー形式の検証 (YYYYMMDDHHMMSS)
    if len(key) != 14 or not key.isdigit():
      return {"success": False, "message": "キー形式が正しくありません。YYYYMMDDHHMMSS形式で入力してください。"}

    # タグの検証
    valid_tags = [tag.value for tag in MemoryTag]
    invalid_tags = [tag for tag in tags if tag not in valid_tags]
    if invalid_tags:
      return {"success": False, "message": f"無効なタグが含まれています: {invalid_tags}", "valid_tags": valid_tags}

    # 優先度の検証
    valid_priorities = [priority.value for priority in MemoryPriority]
    if priority not in valid_priorities:
      return {"success": False, "message": f"無効な優先度です: {priority}", "valid_priorities": valid_priorities}

    memory = memory_manager.add_memory(key, tags, content, priority)
    return {"success": True, "message": "メモリが正常に追加されました", "memory": memory.model_dump()}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("update_memory")
async def update_memory(key: str, tags: List[str], content: str, priority: Optional[str] = None) -> dict:
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
                 Example: "20240115103000"
      tags (List[str]): New list of tags. Only predefined tags are allowed.
                        Example: ["hobby", "learning", "goal"] or ["health", "habit", "preference"]
      content (str): New memory content. Replaces existing content.
      priority (Optional[str]): New priority level ("high", "mid", "low"). If not specified, current priority is maintained.

  Returns:
      dict: Dictionary containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message
          - memory (dict): Information of updated memory (on success)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await update_memory(
      ...     key="20240115103000",
      ...     tags=["hobby", "learning", "goal"],
      ...     content="Continuing guitar practice. Chord positions are gradually improving."
      ... )
      >>> print(result)
      {'success': True, 'message': 'Memory updated successfully', 'memory': {...}}

  Note:
      - Update will not occur if the specified key doesn't exist
      - Updated timestamp is automatically updated
      - Both tags and content are completely replaced
  """
  try:
    # タグの検証
    valid_tags = [tag.value for tag in MemoryTag]
    invalid_tags = [tag for tag in tags if tag not in valid_tags]
    if invalid_tags:
      return {"success": False, "message": f"無効なタグが含まれています: {invalid_tags}", "valid_tags": valid_tags}

    # 優先度の検証（指定されている場合のみ）
    if priority is not None:
      valid_priorities = [priority.value for priority in MemoryPriority]
      if priority not in valid_priorities:
        return {"success": False, "message": f"無効な優先度です: {priority}", "valid_priorities": valid_priorities}

    memory = memory_manager.update_memory(key, tags, content, priority)
    if memory:
      return {"success": True, "message": "メモリが正常に更新されました", "memory": memory.model_dump()}
    else:
      return {"success": False, "message": f"キー {key} のメモリが見つかりません"}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("get_memory")
async def get_memory(key: str) -> dict:
  """
  Retrieve a memory entry with the specified key.

  When to use:
      - When you need to retrieve a specific memory by its exact key
      - When you want to display detailed information about a particular memory
      - When you need to verify the content of an existing memory before updating
      - When building user interfaces that show individual memory details
      - When you want to check if a specific memory exists

  Args:
      key (str): Key of the memory to retrieve. Must be in YYYYMMDDHHMMSS format.
                 Example: "20240115103000"

  Returns:
      dict: Dictionary containing operation result
          - success (bool): Operation success/failure
          - memory (dict): Retrieved memory information (on success)
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await get_memory("20240115103000")
      >>> if result["success"]:
      ...     print(f"Memory content: {result['memory']['content']}")
      ...     print(f"Tags: {result['memory']['tags']}")
      ... else:
      ...     print(f"Error: {result['message']})

  Note:
      - Error is returned if the specified key doesn't exist
      - Memory content, tags, created and updated timestamps are included
  """
  try:
    memory = memory_manager.get_memory_by_key(key)
    if memory:
      return {"success": True, "memory": memory.model_dump()}
    else:
      return {"success": False, "message": f"キー {key} のメモリが見つかりません"}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("search_memories")
async def search_memories(query: str, tags: Optional[List[str]] = None) -> dict:
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
      tags (Optional[List[str]]): Target tags for search. If specified, only memories with these tags are searched.
                                  Example: ["hobby", "learning", "preference"] or None (all tags)

  Returns:
      dict: Dictionary containing search results
          - success (bool): Operation success/failure
          - results (List[dict]): List of search results (on success)
              - key (str): Memory key
              - tags (List[str]): List of tags
              - content (str): Memory content
              - relevance_score (float): Relevance score
          - count (int): Number of search results
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
            # Search by query only
      >>> result = await search_memories("guitar")
      >>> print(f"Search results: {result['count']} items")

      # Search with tag filter
      >>> result = await search_memories("practice", tags=["hobby"])
      >>> for item in result['results']:
      ...     print(f"Relevance: {item['relevance_score']}, Content: {item['content']}")

  Note:
      - Relevance score is calculated as: content match (1.0), tag match (0.8), specified tag match (0.5)
      - Results are sorted by relevance score in descending order
      - Search is possible with empty query if tags are specified
  """
  try:
    results = memory_manager.search_memories(query, tags)
    return {"success": True, "results": [result.model_dump() for result in results], "count": len(results)}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("get_all_memories")
async def get_all_memories() -> dict:
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
      dict: Dictionary containing all memory information
          - success (bool): Operation success/failure
          - memories (List[dict]): List of all memories (on success)
              - key (str): Memory key
              - tags (List[str]): List of tags
              - content (str): Memory content
              - created_at (str): Creation timestamp
              - updated_at (str): Update timestamp
          - count (int): Total number of memories
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await get_all_memories()
      >>> if result["success"]:
      ...     print(f"Total memories: {result['count']} items")
      ...     for memory in result['memories']:
      ...         print(f"Key: {memory['key']}, Tags: {memory['tags']}")
      ...         print(f"Content: {memory['content'][:50]}...")
      ... else:
      ...     print(f"Error: {result['message']})

  Note:
      - Empty list is returned if no memories exist
      - Processing time may increase with large numbers of memories
      - Memories are not guaranteed to be returned in creation order
  """
  try:
    memories = memory_manager.get_all_memories()
    return {"success": True, "memories": [memory.model_dump() for memory in memories], "count": len(memories)}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("delete_memory")
async def delete_memory(key: str) -> dict:
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
      dict: Dictionary containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await delete_memory("20240115103000")
      >>> if result["success"]:
      ...     print("Delete completed:", result["message"])
      ... else:
      ...     print("Delete failed:", result["message"])

  Note:
      - Deleted memories cannot be restored
      - Error is returned if the specified key doesn't exist
      - Memory file is automatically updated after deletion
      - Delete operation cannot be undone
  """
  try:
    success = memory_manager.delete_memory(key)
    if success:
      return {"success": True, "message": f"キー {key} のメモリが削除されました"}
    else:
      return {"success": False, "message": f"キー {key} のメモリが見つかりません"}
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("get_memory_stats")
async def get_memory_stats() -> dict:
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
          - success (bool): Operation success/failure
          - stats (dict): Statistics information (on success)
              - total_memories (int): Total number of memories
              - key_range (dict): Range of keys
                  - earliest (str): Oldest key (YYYYMMDDHHMMSS format)
                  - latest (str): Newest key (YYYYMMDDHHMMSS format)
              - tag_counts (dict): Usage count for each tag
                  - Key: Tag name (e.g., "趣味")
                  - Value: Usage count
              - most_used_tags (List[tuple]): Top 5 most used tags
                  - Each element: Tuple of (tag_name, usage_count)
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await get_memory_stats()
      >>> if result["success"]:
      ...     stats = result["stats"]
      ...     print(f"Total memories: {stats['total_memories']} items")
      ...     print(f"Key range: {stats['key_range']['earliest']} to {stats['key_range']['latest']}")
      ...     print("Popular tags:")
      ...     for tag, count in stats['most_used_tags']:
      ...         print(f"  {tag}: {count} times")
      ... else:
      ...     print(f"Error: {result['message']})

  Note:
      - If no memories exist, total_memories=0 and key_range=None are returned
      - Tag usage count indicates the number of memories with that tag
      - most_used_tags are sorted by usage count in descending order
      - Statistics are calculated in real-time
  """
  try:
    memories = memory_manager.get_all_memories()

    # タグの統計
    tag_counts = {}
    for memory in memories:
      for tag in memory.tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # キー範囲
    keys = [memory.key for memory in memories]
    keys.sort()

    return {
      "success": True,
      "stats": {
        "total_memories": len(memories),
        "key_range": {"earliest": keys[0] if keys else None, "latest": keys[-1] if keys else None},
        "tag_counts": tag_counts,
        "most_used_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
      },
    }
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("get_available_tags")
async def get_available_tags() -> dict:
  """
  Retrieve a list of available tags. Provides 10 predefined category-based tags.

  When to use:
      - When building user interfaces that need to display available tag options
      - When implementing tag selection dropdowns or autocomplete features
      - When you need to validate user input against valid tags
      - When building tag management or configuration interfaces
      - When you want to show users what categories are available for organizing memories
      - When implementing tag-based filtering or categorization features
      - When building help or documentation systems that explain the tag system

  Args:
      None (no parameters required)

  Returns:
      dict: Dictionary containing tag information
          - success (bool): Operation success/failure
          - tags (dict): Category-based tag information (on success)
              - Key: Category name (e.g., "主要カテゴリ")
              - Value: List of tags
                  - value (str): Japanese tag value (e.g., "趣味")
                  - key (str): English tag key (e.g., "HOBBY")
          - total_categories (int): Total number of categories
          - total_tags (int): Total number of tags
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await get_available_tags()
      >>> if result["success"]:
      ...     print(f"Categories: {result['total_categories']}")
      ...     print(f"Total tags: {result['total_tags']}")
      ...     for category, tags in result['tags'].items():
      ...         print(f"\n{category}:")
      ...         for tag in tags:
      ...             print(f"  {tag['value']} ({tag['key']})")
      ... else:
      ...     print(f"Error: {result['message']})

  Note:
      - Currently 10 main category tags are available
      - Each tag includes both Japanese value and English key
      - Tags are categorized as follows:
        hobby, personality, habit, health, learning, relationship, goal, emotion, location, time, preference
      - These tags can be used when adding or updating memories
      - Tag validation is performed automatically, invalid tags are rejected
  """
  try:
    # カテゴリ別にタグを整理
    tag_categories = {"主要カテゴリ": [{"value": tag.value, "key": tag.name} for tag in MemoryTag]}

    return {
      "success": True,
      "tags": tag_categories,
      "total_categories": len(tag_categories),
      "total_tags": sum(len(tags) for tags in tag_categories.values()),
    }
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


@mcp.tool("get_available_priorities")
async def get_available_priorities() -> dict:
  """
  Retrieve a list of available priority levels. Provides 3 predefined priority levels.

  When to use:
      - When building user interfaces that need to display available priority options
      - When implementing priority selection dropdowns or radio buttons
      - When you need to validate user input against valid priority values
      - When building priority management or configuration interfaces
      - When you want to show users what priority levels are available for organizing memories
      - When implementing priority-based filtering or sorting features
      - When building help or documentation systems that explain the priority system

  Args:
      None (no parameters required)

  Returns:
      dict: Dictionary containing priority information
          - success (bool): Operation success/failure
          - priorities (List[str]): List of available priority levels (on success)
              - "high": High priority (最重要)
              - "mid": Medium priority (普通)
              - "low": Low priority (低)
          - total_priorities (int): Total number of priority levels
          - message (str): Error message (on failure)

  Raises:
      Exception: When errors occur

  Example:
      >>> result = await get_available_priorities()
      >>> if result["success"]:
      ...     print(f"Available priorities: {result['priorities']}")
      ...     print(f"Total priority levels: {result['total_priorities']}")
      ... else:
      ...     print(f"Error: {result['message']})

  Note:
      - Currently 3 priority levels are available: high, mid, low
      - High priority memories are displayed first in search results
      - Priority validation is performed automatically, invalid priorities are rejected
      - Priority must be explicitly specified when creating new memories
  """
  try:
    priorities = [priority.value for priority in MemoryPriority]

    return {
      "success": True,
      "priorities": priorities,
      "total_priorities": len(priorities),
    }
  except Exception as e:
    return {"success": False, "message": f"エラーが発生しました: {str(e)}"}


if __name__ == "__main__":
  # Test code
  # import asyncio

  # async def test():
  #     # Test adding memory
  #     result = await add_memory("20240115103000", ["hobby", "learning"], "Started learning guitar")
  #     print("Add memory:", result)
  #
  #     # Test searching memories
  #     result = await search_memories("guitar")
  #     print("Search memories:", result)

  # asyncio.run(test())

  mcp.run(transport="stdio")
