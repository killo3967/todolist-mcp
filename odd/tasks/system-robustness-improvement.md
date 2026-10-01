# Feature: System Robustness and Observability Improvements

**Status**: Done
**Goal**: Upgrade the MCP server from a functional script to a professional-grade, robust, and observable system.

## Problem Statement
The current implementation lacked deep visibility into runtime errors (leading to the `[dedup:ref]` issue) and was susceptible to race conditions when multiple processes (ToDoList, OneDrive, MCP) access the `.tdl` file. The code was also tightly coupled to the XML format.

## Tasks

### 1. Observability: Structured Logging
- [x] Setup a centralized logging configuration (structured text, timestamp | level | module:func:line | message).
- [x] Create a dedicated log file in the project directory (`todolist_mcp.log`).
- [x] Integrate logging into `src/manager.py` (file operations) and `src/tools.py` (MCP entry points).
- [x] Implement a new MCP tool `get_server_logs` to allow the agent to diagnose issues.

### 2. Robustness: Advisory File Locking
- [x] Implement a file-based locking mechanism (`src/lock.py`, `FileLock` via `os.O_CREAT | os.O_EXCL`).
- [x] Integrate locking into the read/write cycles (`XmlTodoRepository.load_all` and `save_all`).
- [x] Add retry logic with exponential backoff and jitter when a lock is held.

### 3. Scalability: Layered Architecture
- [x] Define Domain Models (`src/domain/models.py`: `Task`, `Priority`).
- [x] Implement XML Repository (Data Mapper) in `src/infrastructure/repository.py` (`XmlTodoRepository`).
- [x] Refactor the manager into a Service Layer (`src/services/todo_service.py`, `TodoService`); `src/manager.py` is now a compatibility shim.

## Evidence
- `test_atomic_logic.py` -> atomic `os.replace` write works.
- `test_direct_tool.py` -> direct tool execution changes the file `mtime` and persists content.
- `repro_mcp_tool.py` -> MCP-path `add_task` inserts the task successfully.
- `todolist_mcp.log` created and populated; `get_server_logs` exposes it over MCP.
- `pi mcp list` reports the `todolist` server connected with 17 tools, including `get_server_logs`.

## Knowledge & Observations
- Initial investigation showed that `os.replace` (atomic writes) helped, but full concurrency protection requires explicit locking.
- Error masking via `[dedup:ref]` is a key driver for the logging requirement.
- Layering separates persistence (repository) from business rules (service) and data (domain), which also made the lock integration a single-point change.

## Outstanding
- None of this work is committed yet (see working tree status).
