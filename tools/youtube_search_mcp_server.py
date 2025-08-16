import os

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

API_KEY = os.environ.get("GOOGLE_API_KEY", "")
print("^^^^^^^^^^^^^^^^^^^^^^^^")
print(API_KEY)
print("^^^^^^^^^^^^^^^^^^^^^^^^")

MAX_RESULTS = 10

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"


# for remote server
# mcp = FastMCP(
#   "youtube_search_mcp_server",
#   host="localhost",
#   port=10001,
#   stateless_http=True,
# )


class YouTubeSearchResult(BaseModel):
  title: str = Field(..., description="Title of the video")
  description: str = Field(..., description="Description of the video")
  video_url: str = Field(..., description="Video URL of the video")


mcp = FastMCP("youtube_search_mcp_server")


@mcp.tool("youtube_search")
async def youtube_search(query: str, max_results: int = 3) -> list[YouTubeSearchResult]:
  """
  Search for videos on YouTube.

  Args:
    query: The search query.
    max_results: The maximum number of results to return.
  """
  # ステップ1: 動画IDの取得（検索）
  search_params = {"part": "snippet", "q": query, "type": "video", "maxResults": max_results, "key": API_KEY}
  response = requests.get(SEARCH_URL, params=search_params).json()
  if "items" not in response:
    return []

  video_ids = [item["id"]["videoId"] for item in response["items"]]

  # ステップ2: 動画情報の取得（詳細）
  video_params = {"part": "snippet", "id": ",".join(video_ids), "key": API_KEY}

  video_res = requests.get(VIDEO_URL, params=video_params).json()

  # 結果出力
  videos: list[YouTubeSearchResult] = []
  for item in video_res["items"]:
    video = YouTubeSearchResult(
      title=item["snippet"]["title"],
      description=item["snippet"]["description"],
      video_url=f"https://www.youtube.com/watch?v={item['id']}",
    )
    videos.append(video)

  return videos


if __name__ == "__main__":
  # import asyncio

  # result = asyncio.run(youtube_search("bob marley guiter 練習", 3))
  # print(result)
  mcp.run(transport="stdio")

  # for remote
  # mcp.run(transport="streamable-http")
