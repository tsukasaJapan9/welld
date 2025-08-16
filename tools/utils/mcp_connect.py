import asyncio
import logging

from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters
from rich import print

# ADDED: Import signal and sys for graceful shutdown handling
from utilities.mcp.mcp_discovery import MCPDiscovery

# ADDED: Configure logging for MCP cleanup issues to reduce noise during shutdown
logging.getLogger("mcp").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


import json
import os
from typing import Any, Dict


class MCPDiscovery:
  """
  Reads a JSON config file defining MCP servers and provides access
  to the server definitions under the "mcpServers" key

  Attributes:
      config_file (str): Path to the JSON configuration file.
      config (Dict[str, Any]): Parsed JSON content, expected to contain the "mcpServers" key.
  """

  def __init__(self, config_file: str = None):
    """
    Initializes the MCPDiscovery with a configuration file.

    Args:
        config_file (str, optional): Path to the JSON configuration file.
        If None, defaults to 'mcp_config.json'
        located in the same directory as this module.
    """
    if config_file is None:
      self.config_file = os.path.join(os.path.dirname(__file__), "mcp_config.json")
    else:
      self.config_file = config_file

    self.config = self._load_config()

  def _load_config(self) -> Dict[str, Any]:
    try:
      with open(self.config_file, "r") as f:
        data = json.load(f)

      if not isinstance(data, dict):
        raise ValueError(f"Invalid configuration format in {self.config_file}")

      return data
    except FileNotFoundError:
      raise FileNotFoundError(f"Configuration file {self.config_file} not found.")
    except Exception as e:
      raise RuntimeError(f"Error reading configuration file {self.config_file}: {e}")

  def list_servers(self) -> Dict[str, Any]:
    """
    Returns the MCP servers defined in the configuration file.

    Returns:
        Dict[str, Any]: The content of the "mcpServers" key from the config.

    Raises:
        KeyError: If "mcpServers" key is not found in the configuration.
    """
    if "mcpServers" not in self.config:
      raise KeyError(f"'mcpServers' key not found in {self.config_file}")

    return self.config.get("mcpServers", {})


class MCPConnector:
  """
  Discovers the MCP servers from the config.
  Config will be loaded by the MCP discovery class
  Then it lists each server's tools
  and then caches them as MCPToolsets that are compatible with
  Google's Agent Development Kit
  """

  def __init__(self, config_file: str = None):
    self.discovery = MCPDiscovery(config_file=config_file)
    self.tools: list[MCPToolset] = []

  async def _load_all_tools(self):
    """
    Loads all tools from the discovered MCP servers
    and caches them as MCPToolsets.
    """

    tools = []

    for name, server in self.discovery.list_servers().items():
      try:
        if server.get("command") == "streamable_http":
          conn = StreamableHTTPServerParams(url=server["args"][0])
        else:
          conn = StdioConnectionParams(
            server_params=StdioServerParameters(command=server["command"], args=server["args"]), timeout=5
          )

        # ADDED: Wrap toolset creation with timeout and error handling
        # This prevents hanging on unresponsive MCP servers
        toolset = await asyncio.wait_for(MCPToolset(connection_params=conn).get_tools(), timeout=10.0)

        if toolset:
          # Create the actual toolset object for caching
          mcp_toolset = MCPToolset(connection_params=conn)
          tool_names = [tool.name for tool in toolset]
          print(f"[bold green]Loaded tools from server [cyan]'{name}'[/cyan]:[/bold green] {', '.join(tool_names)}")
          tools.append(mcp_toolset)

      # ADDED: Specific error handling for different types of connection failures
      except asyncio.TimeoutError:
        print(f"[bold red]Timeout loading tools from server '{name}' (skipping)[/bold red]")
      except ConnectionError as e:
        print(f"[bold red]Connection error loading tools from server '{name}': {e} (skipping)[/bold red]")
      except Exception as e:
        print(f"[bold red]Error loading tools from server '{name}': {e} (skipping)[/bold red]")

    self.tools = tools

  async def get_tools(self) -> list[MCPToolset]:
    """
    Returns the cached list of MCPToolsets.
    """

    await self._load_all_tools()
    return self.tools.copy()
