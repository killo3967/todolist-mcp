"""Backward-compatibility entry point.

For new deployments, use main.py instead.
"""

from src.tools import mcp

if __name__ == "__main__":
    mcp.run()
