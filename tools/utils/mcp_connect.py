import asyncio
import copy
import json
import logging
from typing import Any, Dict

from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)


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

  async def _load_all_tools(self) -> list[MCPToolset]:
    tools: list[MCPToolset] = []

    for name, server in self.discovery.list_servers().items():
      try:
        if server.get("type") == "streamable_http":
          conn = StreamableHTTPServerParams(url=server["args"][0])
        else:
          conn = StdioConnectionParams(
            server_params=StdioServerParameters(command=server["command"], args=server["args"]), timeout=5
          )

        toolset = await asyncio.wait_for(MCPToolset(connection_params=conn).get_tools(), timeout=10.0)

        if toolset:
          mcp_toolset = MCPToolset(connection_params=conn)
          tools.append(mcp_toolset)

      except asyncio.TimeoutError:
        logger.error(f"Timeout loading tools from server '{name}' (skipping)")
      except ConnectionError as e:
        logger.error(f"Connection error loading tools from server '{name}': {e} (skipping)")
      except Exception as e:
        logger.error(f"Error loading tools from server '{name}': {e} (skipping)")

    return tools

  async def get_tools(self) -> list[MCPToolset]:
    tools = await self._load_all_tools()
    return copy.deepcopy(tools)
