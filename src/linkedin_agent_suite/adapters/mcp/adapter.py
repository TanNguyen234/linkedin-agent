"""Thin MCP adapter wrapping LinkedIn Agent Suite services."""

try:
    import fastmcp  # type: ignore[import-not-found]
except ImportError:
    fastmcp = None  # Graceful fallback when FastMCP is not installed


def create_mcp_server():
    """Create FastMCP server instance if installed."""
    if fastmcp is None:
        raise RuntimeError("FastMCP is not installed. Run with [mcp] extra.")
    mcp = fastmcp.FastMCP("LinkedIn Agent Suite")
    return mcp
