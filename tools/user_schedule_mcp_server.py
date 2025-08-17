import datetime
import json
import os
import re
import uuid
from datetime import timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

JST = timezone(timedelta(hours=9), name="JST")


class SchedulePriority(Enum):
  """Schedule priority levels"""

  HIGH = "high"
  MID = "mid"
  LOW = "low"


class ScheduleEntry(BaseModel):
  """Schedule entry"""

  deadline: str = Field(..., description="Schedule deadline")
  content: str = Field(..., description="Schedule content")
  priority: str = Field(..., description="Schedule priority (high: high, mid: mid, low: low)")
  created_at: str = Field(..., description="Schedule created at")
  updated_at: str = Field(..., description="Schedule updated at")


class ScheduleSearchResult(BaseModel):
  """Schedule search result"""

  schedule_id: str = Field(..., description="Schedule ID")
  deadline: str = Field(..., description="Schedule deadline")
  content: str = Field(..., description="Schedule content")
  priority: str = Field(..., description="Schedule priority (high: high, mid: mid, low: low)")
  created_at: str = Field(..., description="Schedule created at")
  updated_at: str = Field(..., description="Schedule updated at")


class ScheduleManager:
  """メモリの管理を行うクラス"""

  def __init__(self, schedule_file: str = "user_schedule.json"):
    self.schedule_file = Path(schedule_file)
    # スケジュールディレクトリを自動作成
    self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
    self.schedules: dict[str, ScheduleEntry] = {}
    self._load_schedules()

  def _load_schedules(self):
    """スケジュールファイルからデータを読み込む"""
    if self.schedule_file.exists():
      try:
        with open(self.schedule_file, "r", encoding="utf-8") as f:
          data = json.load(f)
          for key, item in data.items():
            # 過去のデータにpriorityフィールドがない場合は"mid"をデフォルト値として設定
            if "priority" not in item:
              item["priority"] = "mid"
            try:
              self.schedules[key] = ScheduleEntry(**item)
            except Exception as e:
              print(f"Warning: Failed to load schedule item: {e}, item: {item}")
              continue
      except (json.JSONDecodeError, KeyError):
        self.schedules = {}
    else:
      self.schedules = {}

  def _save_schedules(self):
    """スケジュールをファイルに保存する"""
    self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
    # ScheduleEntryオブジェクトを辞書形式に変換して保存
    schedules_dict = {key: schedule.model_dump() for key, schedule in self.schedules.items()}
    with open(self.schedule_file, "w", encoding="utf-8") as f:
      json.dump(schedules_dict, f, ensure_ascii=False, indent=2)

  def add_schedule(self, deadline: str, content: str, priority: str) -> bool:
    """新しいスケジュールを追加"""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    schedule_id = str(uuid.uuid4())
    schedule = ScheduleEntry(
      deadline=deadline,
      content=content,
      priority=priority,
      created_at=now,
      updated_at=now,
    )
    self.schedules[schedule_id] = schedule
    self._save_schedules()
    return True

  def update_schedule(self, schedule_id: str, content: str) -> bool:
    """指定されたキーのスケジュールを更新"""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if schedule_id in self.schedules.keys():
      self.schedules[schedule_id].content = content
      self.schedules[schedule_id].updated_at = now
      self._save_schedules()
      return True
    return False

  def get_schedule_by_key(self, schedule_id: str) -> Optional[ScheduleEntry]:
    """指定されたキーのスケジュールを取得"""
    return self.schedules.get(schedule_id)

  def search_schedules(self, before_date: int, after_date: int) -> List[ScheduleSearchResult]:
    """スケジュールを検索"""
    results: List[ScheduleSearchResult] = []

    # 今日の日付を基準に検索範囲を計算
    today = datetime.datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = (today - datetime.timedelta(days=before_date)).strftime("%Y%m%d")
    end_date = (today + datetime.timedelta(days=after_date)).strftime("%Y%m%d")

    # 指定された期間内のスケジュールをフィルタリング
    filtered_schedules: dict[str, ScheduleEntry] = {}
    for key, schedule in self.schedules.items():
      schedule_date = schedule.deadline[:8]  # YYYYMMDD部分を取得
      if start_date <= schedule_date <= end_date:
        filtered_schedules[key] = schedule

    for key, schedule in filtered_schedules.items():
      results.append(
        ScheduleSearchResult(
          schedule_id=key,
          deadline=schedule.deadline,
          content=schedule.content,
          priority=schedule.priority,
          created_at=schedule.created_at,
          updated_at=schedule.updated_at,
        )
      )
    return results

  def get_all_schedules(self) -> List[ScheduleSearchResult]:
    """全てのメモリを取得"""
    return [
      ScheduleSearchResult(
        schedule_id=key,
        deadline=schedule.deadline,
        content=schedule.content,
        priority=schedule.priority,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
      )
      for key, schedule in self.schedules.items()
    ]

  def delete_schedule(self, schedule_id: str) -> bool:
    """指定されたキーのスケジュールを削除"""
    if schedule_id in self.schedules:
      del self.schedules[schedule_id]
      self._save_schedules()
      return True
    return False


# 環境変数からメモリファイルの保存場所を取得
USER_SCHEDULE_FILE = os.environ.get("USER_SCHEDULE_FILE", "memory/user_schedule.json")

# スケジュールマネージャーのインスタンス
schedule_manager = ScheduleManager(USER_SCHEDULE_FILE)

# MCPサーバーの作成
mcp = FastMCP("user_schedule_mcp_server", log_level="ERROR")


@mcp.tool("add_schedule")
async def add_schedule(deadline: str, content: str, priority: str) -> Tuple[bool, str]:
  """
  Add a new schedule with user's information.

  When to use:
      - When you want to record a new schedule
      - When creating the first entry for a specific event or moment
      - When you want to track progress or changes over time

  Args:
      deadline (str): Schedule deadline. Must be in YYYYMMDDHHMM format.
                 Example: "202401151030"
      content (str): Schedule content. Provide detailed description.
      priority (str): Priority level ("high", "mid", "low"). Must be specified.

  Returns:
      Tuple[bool, str]: Tuple containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message
  """
  try:
    # 日付の検証
    if not re.match(r"^\d{12}$", deadline):
      return False, "Invalid deadline format. Must be in YYYYMMDDHHMM format."
    # 優先度の検証
    valid_priorities = [priority.value for priority in SchedulePriority]
    if priority not in valid_priorities:
      return False, f"Invalid priority: {priority}"

    is_success = schedule_manager.add_schedule(deadline, content, priority)
    return is_success, "Success to add schedule"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("update_schedule")
async def update_schedule(schedule_id: str, content: str) -> Tuple[bool, str]:
  """
  Update a schedule entry with the specified key.

  When to use:
      - When you need to modify existing schedule content
      - When updating progress or status of an ongoing activity
      - When correcting or refining previously recorded information

  Args:
      schedule_id (str): Key of the schedule to update. Must be in YYYYMMDDHHMMSS format.
                 Example: "schedule_20240115103000"
      content (str): New schedule content. Replaces existing content.

  Returns:
      Tuple[bool, str]: Tuple containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message

  """
  try:
    is_success = schedule_manager.update_schedule(schedule_id, content)
    if is_success:
      return True, "Success to update schedule"
    else:
      return False, "Failed to update schedule"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("search_schedules")
async def search_schedules(before_date: int, after_date: int) -> List[ScheduleSearchResult]:
  """
  Search schedules with flexible query.

  When to use:
      - When you want to find schedules containing specific keywords or phrases

  Args:
      before_date (int): Search query. Specify the number of days before today.
                   Example: 10
      after_date (int): Search query. Specify the number of days after today.
                   Example: 10

  Returns:
      List[ScheduleSearchResult]: List of search results
  """
  try:
    results = schedule_manager.search_schedules(before_date, after_date)
    return results
  except Exception:
    return []


@mcp.tool("get_all_schedules")
async def get_all_schedules() -> List[ScheduleSearchResult]:
  """
  Retrieve all stored schedule entries.

  When to use:
      - When you need to display a complete list of all schedules
      - When building dashboards or overview pages
      - When you want to analyze all stored data for patterns or insights
      - When performing bulk operations on all schedules
      - When you need to export or backup all schedule data
      - When building administrative interfaces for schedule management

  Args:
      None (no parameters required)

  Returns:
      List[ScheduleSearchResult]: List of all schedules
  """
  try:
    schedules = schedule_manager.get_all_schedules()
    return schedules
  except Exception:
    return []


@mcp.tool("delete_schedule")
async def delete_schedule(schedule_id: str) -> Tuple[bool, str]:
  """
  Delete a schedule entry with the specified key.

  When to use:
      - When you need to remove incorrect or outdated information
      - When cleaning up test data or temporary entries

  Args:
      schedule_id (str): Key of the schedule to delete. Must be in YYYYMMDDHHMMSS format.
                 Example: "20240115103000"

  Returns:
      Tuple[bool, str]: Tuple containing operation result
          - success (bool): Operation success/failure
          - message (str): Result message

  """
  try:
    is_success = schedule_manager.delete_schedule(schedule_id)
    if is_success:
      return True, "Success to delete schedule"
    else:
      return False, "Failed to delete schedule"
  except Exception as e:
    return False, f"Error: {str(e)}"


@mcp.tool("get_schedule_priority_list")
async def get_schedule_priority_list() -> List[str]:
  """
  Get the list of available priorities.
  """
  return [priority.value for priority in SchedulePriority]


if __name__ == "__main__":
  # Test code
  # import asyncio

  # schedule_manager = ScheduleManager(schedule_file="/home/tsukasa/works/welld/memory/user_schedule.json")

  # async def test():
  #   # Test adding memory
  #   schedule1 = await add_schedule("202508171000", "meeting with John", "high")
  #   print("Add schedule:", schedule1)

  #   schedule2 = await add_schedule("202508181000", "meeting with Taro", "high")
  #   print("Add schedule:", schedule2)

  #   schedule3 = await add_schedule("202508161000", "meeting with Jiro", "high")
  #   print("Add schedule:", schedule3)

  #   all_schedules = await get_all_schedules()
  #   print("All schedules:", all_schedules)

  #   search_result = await search_schedules(1, 1)
  #   print("Search result:", search_result)

  #   for schedule in all_schedules:
  #     delete_result = await delete_schedule(schedule.schedule_id)
  #     print("Delete result:", delete_result)

  # asyncio.run(test())

  mcp.run(transport="stdio")
