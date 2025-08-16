import asyncio
import json
import logging
import os
from typing import Any, Dict

from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class MCPDiscovery:
  def __init__(self, config_file: str):
    self.config_file = config_file
    self.config = self._load_config()

  def _load_config(self) -> Dict[str, Any]:
    try:
      with open(self.config_file, "r") as f:
        return json.load(f)
    except FileNotFoundError:
      raise FileNotFoundError(f"Configuration file {self.config_file} not found.")
    except Exception as e:
      raise RuntimeError(f"Error reading configuration file {self.config_file}: {e}")

  def list_servers(self) -> Dict[str, Any]:
    if "mcpServers" not in self.config:
      raise KeyError(f"'mcpServers' key not found in {self.config_file}")

    return self.config.get("mcpServers", {})


class MCPConnector:
  def __init__(self, config_file: str = "./config/mcp_config.json"):
    self.discovery = MCPDiscovery(config_file=config_file)

  async def _load_http_all_tools(self) -> tuple[list[str], list[MCPToolset]]:
    tools: list[MCPToolset] = []
    names: list[str] = []

    for name, server in self.discovery.list_servers().items():
      try:
        if server.get("command") == "streamable_http":
          conn = StreamableHTTPServerParams(url=server["args"][0])
        else:
          conn = StdioConnectionParams(
            server_params=StdioServerParameters(command=server["command"], args=server["args"], env=server["env"]),
            timeout=5,
          )

        toolset = await asyncio.wait_for(MCPToolset(connection_params=conn).get_tools(), timeout=10.0)
        if toolset:
          mcp_toolset = MCPToolset(connection_params=conn)
          tools.append(mcp_toolset)
          names.append(name)

      except asyncio.TimeoutError:
        logger.error(f"Timeout loading tools from server '{name}' (skipping)")
      except ConnectionError as e:
        logger.error(f"Connection error loading tools from server '{name}': {e} (skipping)")
      except Exception as e:
        logger.error(f"Error loading tools from server '{name}': {e} (skipping)")

    return names, tools

  def _load_stdio_all_tools(self) -> tuple[list[str], list[MCPToolset]]:
    tools: list[MCPToolset] = []
    names: list[str] = []

    for name, server in self.discovery.list_servers().items():
      if server.get("command") == "streamable_http":
        continue

      try:
        if "env" in server and "GOOGLE_API_KEY" in server["env"]:
          server["env"]["GOOGLE_API_KEY"] = GOOGLE_API_KEY

        conn = StdioConnectionParams(
          server_params=StdioServerParameters(
            command=server["command"], args=server["args"], env=server["env"] if "env" in server else None
          )
        )
        tool = MCPToolset(connection_params=conn)
        tools.append(tool)
        names.append(name)
      except Exception as e:
        logger.error(f"Error loading tools from server '{name}': {e} (skipping)")

    return names, tools

  async def get_http_tools(self) -> tuple[list[str], list[MCPToolset]]:
    names, tools = await self._load_http_all_tools()
    return names, tools.copy()

  def get_stdio_tools(self) -> tuple[list[str], list[MCPToolset]]:
    names, tools = self._load_stdio_all_tools()
    return names, tools.copy()
