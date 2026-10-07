"""Thin, optional FastMCP adapter."""
def create_mcp_server():
    try:
        from fastmcp import FastMCP
        mcp = FastMCP(name="linkedin-agent-suite")
        return mcp
    except ImportError:
        return None
