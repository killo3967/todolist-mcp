"""Hot tests for analyze_structure MCP tool (no parameters)."""


def test_analyze_structure(mcp):
    client, _ = mcp
    result = client.call_tool("analyze_structure", {})
    text = result["result"]["content"][0]["text"]
    assert "Root Element: TODOLIST" in text
    assert "Project Name: test-hot" in text
    assert "Next Unique ID:" in text
    assert "Tasks:" in text
    assert "Categories:" in text
    assert "Sample Task Attributes:" in text
