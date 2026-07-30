"""Hot tests for read_any_tdl_file MCP tool."""


def test_read_any_tdl_file_markdown(mcp):
    """Read the test file explicitly by path."""
    client, tdl_path = mcp
    result = client.call_tool("read_any_tdl_file", {"file_path": str(tdl_path)})
    text = result["result"]["content"][0]["text"]
    assert "Task Alpha" in text
    assert "Task Beta" in text


def test_read_any_tdl_file_json(mcp):
    client, tdl_path = mcp
    result = client.call_tool("read_any_tdl_file", {
        "file_path": str(tdl_path),
        "format": "json",
    })
    import json
    data = json.loads(result["result"]["content"][0]["text"])
    assert isinstance(data, list)
    assert len(data) >= 4


def test_read_any_tdl_file_nonexistent(mcp):
    client, _ = mcp
    result = client.call_tool("read_any_tdl_file", {
        "file_path": "Z:/nonexistent/file.tdl",
    })
    text = result["result"]["content"][0]["text"]
    assert "Error" in text or "not found" in text.lower() or "no such" in text.lower()


def test_read_any_tdl_file_path_traversal_blocked(mcp):
    """Path traversal with '..' should be blocked."""
    client, tdl_path = mcp
    # Try to escape with ..
    traversal = str(tdl_path.parent / ".." / "secret.txt")
    result = client.call_tool("read_any_tdl_file", {"file_path": traversal})
    text = result["result"]["content"][0]["text"]
    assert "traversal" in text.lower() or "blocked" in text.lower() or "Error" in text
