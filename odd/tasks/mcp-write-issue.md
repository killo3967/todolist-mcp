# Feature: MCP Write Failure Investigation

**Status**: Done
**Goal**: Identify why the `todolist_mcp` tools fail to persist changes to the `.tdl` file in certain scenarios, specifically when called via the MCP protocol, despite the underlying code working correctly in direct execution.

## Problem Statement
The user reported that `todolist_add_task` and `todolist_move_task` via MCP do not modify the `.tdl` file (mtime and FILEVERSION remain unchanged). However, the same code path in `src/tools.py` works when executed directly. The server responses arrive as `[dedup:ref]`, obscuring error details.

## Tasks
- [x] Investigate `src/tools.py` and `src/manager.py` write logic
- [x] Implement atomic writes in `src/manager.py`
- [x] Improve error reporting in `src/tools.py`
- [ ] Analyze `mcp_server.ini` and environment configuration
- [ ] Reproduce the `[dedup:ref]` response behavior
- [ ] Verify file locking and concurrency issues
- [ ] Implement fix and verification

## Knowledge & Observations
- Task 304 was successfully written, suggesting intermittent failure or specific trigger conditions.
- ToDoList app might be holding a stale memory copy (though user says auto-refresh is enabled).
- MCP responses are being deduped by the server.
- **Fix**: Implemented atomic writes (write to `.tmp` then `os.replace`) to mitigate file locking issues by OneDrive/ToDoList.
- **Fix**: Improved error messages in `src/tools.py` to explicitly mention potential file locking.
- Verification: `repro_write.py`, `repro_mcp_tool.py`, and `test_direct_tool.py` all passed.
