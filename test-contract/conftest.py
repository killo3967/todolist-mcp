"""Hot-test infrastructure: black-box MCP contract tests via stdio subprocess.

Each test:
1. Copies test_contract.tdl to a temp file
2. Sets TODOLIST_FILE env var
3. Spawns tdl_mcp_server.py as subprocess
4. Talks JSON-RPC over stdin/stdout
5. Verifies the .tdl file was mutated correctly
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

CONTRACT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CONTRACT_DIR.parent
SERVER_SCRIPT = PROJECT_DIR / "main.py"
TEMPLATE_TDL = CONTRACT_DIR / "test_contract.tdl"
VENV_PYTHON = PROJECT_DIR / "venv" / "Scripts" / "python.exe"


def _read_exactly(stream, size):
    """Read exactly `size` bytes from a stream, blocking until done."""
    data = b""
    while len(data) < size:
        chunk = stream.read(size - len(data))
        if not chunk:
            break
        data += chunk
    return data


class MCPClient:
    """Minimal JSON-RPC MCP client over stdio."""

    def __init__(self, process):
        self.process = process
        self._next_id = 1

    def send(self, method, params=None):
        """Send a JSON-RPC request and return the response."""
        req_id = self._next_id
        self._next_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }
        payload = json.dumps(request) + "\n"
        self.process.stdin.write(payload)
        self.process.stdin.flush()

        # Read response line
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Server closed stdout unexpectedly")
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response

    def initialize(self):
        """Perform MCP handshake."""
        return self.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-contract", "version": "1.0"},
        })

    def list_tools(self):
        return self.send("tools/list")

    def call_tool(self, name, arguments):
        return self.send("tools/call", {
            "name": name,
            "arguments": arguments,
        })

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()


@pytest.fixture
def mcp(tmp_path):
    """Spawn the MCP server pointed at a fresh copy of test_contract.tdl."""
    # Copy template .tdl to temp
    tdl_copy = tmp_path / "test_contract.tdl"
    shutil.copy2(TEMPLATE_TDL, tdl_copy)

    env = os.environ.copy()
    env["TODOLIST_FILE"] = str(tdl_copy)

    proc = subprocess.Popen(
        [str(VENV_PYTHON), str(SERVER_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        encoding="utf-8",
    )

    client = MCPClient(proc)

    # MCP handshake
    client.initialize()

    yield client, tdl_copy

    # Teardown
    try:
        client.close()
    except Exception:
        proc.kill()
