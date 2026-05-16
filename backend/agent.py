import os
import sys
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

load_dotenv()

# Define the connection to the local MCP server
mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
mcp_config = StdioConnectionParams(
    server_params=StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path],
        env=os.environ.copy()
    ),
    timeout=30.0
)

# System instruction for the agent
system_instruction = (
    "You are a GitHub profile analyst and dev card generator. "
    "When a user gives you a GitHub username, you ALWAYS follow this exact sequence: "
    "first call scrape_github, then analyze_profile with the result, "
    "then generate_card_html with all three inputs, then save_card. "
    "Never skip steps. Be enthusiastic about developers' work. "
    "If the profile is private or doesn't exist, say so clearly."
)

# Create the ADK Agent
github_card_agent = Agent(
    name="github_card_agent",
    model="gemini-2.5-flash",
    instruction=system_instruction,
    tools=[McpToolset(connection_params=mcp_config)]
)
