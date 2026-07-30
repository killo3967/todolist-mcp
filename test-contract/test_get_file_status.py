"""Hot tests for get_file_status MCP tool (no parameters)."""


def test_get_file_status(mcp):
    client, _ = mcp
    result = client.call_tool("get_file_status", {})
    text = result["result"]["content"][0]["text"]
    assert "ToDoList File Status" in text
    assert "Project: test-contract" in text
    assert "Total Tasks:" in text
    assert "Completed:" in text
    assert "Remaining:" in text
