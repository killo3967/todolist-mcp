# Feature: Migrate Legacy Unit Tests to the Service-Layer Architecture

## Goal
Bring the legacy unit suite (`test/`) back to green by pointing it at the real
implementation — `TodoService` + `XmlTodoRepository` (+ `src/domain` models and
the `src/tools.py` helpers) — instead of the old monolithic `ToDoListManager`.

End state: a single implementation of the business logic and a single, coherent
test story (`pytest test/ test-contract/` fully green).

## Why
- `test-contract/` (109 tests) is green and covers the public MCP behaviour end to end.
- `test/` (86 tests) is red: **57 failed / 29 passed**. It imports
  `from src.manager import ToDoListManager` and exercises the OLD manager API.
- Earlier in this session the architecture was refactored: business logic moved to
  `src/services/todo_service.py` + `src/infrastructure/repository.py`, and
  `src/manager.py` (≈600 lines at `HEAD`) was reduced to a shim with stubbed
  leftovers (`_decode_priority` returns `p`, `_write_comments` is `pass`, ...).
- The legacy tests were never migrated, so they assert against dead stubs.

## Decision (recorded)
**Migrate the tests. Do NOT restore the legacy manager API.**
Restoring it would re-create ~600 lines of duplicated logic (date/priority/status
codecs, position math, search, update) already owned by `TodoService` and
`XmlTodoRepository`. Two sources of truth for the same behaviour guarantee silent
divergence. Tests adapt to the implementation; never the reverse.

## Scope
### In scope
- Retarget legacy unit tests to the new classes/functions.
- Update assertions that encode behaviour intentionally changed by the contract
  (default formats, error strings, `date` vs `datetime`).
- Reduce `src/manager.py` to wiring only.

### Out of scope
- Changing `test-contract/` expectations.
- Adding new product behaviour.
- Reintroducing the old manager API surface.

## Work Units
| # | Work unit | Target under test | Legacy tests |
|---|-----------|-------------------|--------------|
| WU1 | Codecs | `XmlTodoRepository._decode_date/_encode_date/_decode_status`, `Priority.from_str`, `_hex_to_bgr` | `TestDateCodec` (7), `TestPriorityCodec` (5), `TestDecodeStatus` (5), `TestHexToRGBInt` (4) |
| WU2 | Positions & hierarchy | `TodoService._find_task_by_pos`, `_find_parent_of_task`, `_recalculate_positions`; root `NEXTUNIQUEID` round-trip | `TestFindTaskByPosString` (6), `TestFindParent` (3), `TestUpdatePositions` (2), `TestNextUniqueId` (2) |
| WU3 | Search & date filter | `TodoService.search_tasks`, `TodoService.get_today_tasks` | `TestSearchTasks` (9), `TestFilterTasksByDate` (3) |
| WU4 | Parse / extract | `XmlTodoRepository.load_all` | `TestExtractTasks` (6), `TestParseTdlFile` (3) |
| WU5 | Mutations | `TodoService.add_comment`, `TodoService.update_task` | `TestAddComment` (3), `TestUpdateTask` (13) |
| WU6 | Markdown rendering | `src/tools.py` markdown builders | `TestFormatTasksAsMarkdown` (4) |
| WU7 | Shim trim + end-to-end | `src/manager.py` wiring only; `test_server.py`, `test_update_functionality.py` | `test_server.py` (4), `test_update_functionality.py` (1) |
| — | Unchanged | `_resolve_tdl_file` resolution | `test_resolve_tdl.py` (6) — already green, keep as-is |

## Constraint Checklist (per work unit)
- [ ] No production logic duplicated into tests or back into `src/manager.py`.
- [ ] Tests assert the CURRENT contract, not the old one.
- [ ] `pytest test-contract/` stays green after every work unit.
- [ ] Each work unit closes with a work-unit commit (only when the user authorizes commits).

## Verification
- `pytest test-contract/ -q` → must remain **109 passed**.
- `pytest test/ -q` → must progress toward **0 failed**; final target **86 passed**.
- Final: `pytest test/ test-contract/ -q` → all green.

## Relevant Files
- `test/test_tdl_mcp_server.py` (75 tests, main migration target)
- `test/test_server.py` (4), `test/test_update_functionality.py` (1)
- `test/test_resolve_tdl.py` (6, unchanged)
- `src/services/todo_service.py`, `src/infrastructure/repository.py`
- `src/domain/models.py`, `src/tools.py`, `src/manager.py`

## Progress Log
- 2026-10-01 — Feature created. Baseline: `test-contract/` 109 passed; `test/` 29 passed / 57 failed.
- 2026-10-01 — **WU1 done** (codecs). Migrated `TestDateCodec`, `TestPriorityCodec`, `TestHexToRGBInt`→`TestHexToBgr`, `TestDecodeStatus` to `XmlTodoRepository`, `Priority`, `_hex_to_bgr`. Test-file-only change. `test/` → 45 passed / 40 failed. `test-contract/` stays 109.
- 2026-10-01 — **WU2 done** (positions & hierarchy). Migrated `TestFindTaskByPosString`, `TestFindParent`, `TestUpdatePositions`, `TestNextUniqueId` to `TodoService` / `XmlTodoRepository.load_all`. Test-file-only change. `test/` → 55 passed / 31 failed. `test-contract/` stays 109.
- 2026-10-01 — **WU3 done** (search & date filter). Production: restored the `allocated_to` filter in `TodoService.search_tasks` and in the `search_tasks` MCP tool; added contract test `test_search_by_allocated_to`. Migrated `TestSearchTasks`, `TestFilterTasksByDate`.
- 2026-10-01 — **WU4 done** (parse/extract). Production fix: `save_all` now writes root `<TODOLIST>` (was `<TODO>`). Added a round-trip regression test that would have caught it. Migrated `TestExtractTasks`, `TestParseTdlFile`.
- 2026-10-01 — **WU5 done** (mutations). Migrated `TestAddComment`, `TestUpdateTask` to `TodoService.add_comment` / `update_task`. Test-file-only change.
- 2026-10-01 — **WU6 done** (markdown). Production: extracted recursive `_format_tasks_markdown` and restored 2-space subtask nesting across all markdown paths. Migrated `TestFormatTasksAsMarkdown`.
- 2026-10-01 — **WU7 done** (shim + end-to-end). `src/manager.py` reduced to wiring only (`_resolve_tdl_file`, `DEFAULT_TDL_FILE`, repository+service composition). Migrated `test_server.py`; rewrote `test_update_functionality.py` as an isolated temp-file test. `test/test_tdl_mcp_server.py` fully decoupled from the manager.
- 2026-10-01 — **Final verification**: `pytest test/ test-contract/` → **196 passed** (test/ 86, test-contract/ 110). Zero failures.

## Decisions (all three resolved 2026-10-01: restore)
The migration surfaced three places where the refactor changed behaviour beyond the tests. The user chose to restore all three. Each item below is now FIXED in production and covered by a test; the text records the original problem.

1. **WU3 — `allocated_to` search filter removed.** `TodoService.search_tasks(query, category, priority, completed, status)` has no `allocated_to`; the legacy `TestSearchTasks::test_filter_by_assigned_to` therefore has no target. Options: (a) drop the test as an intentional feature removal, (b) re-add an `allocated_to` filter to service + MCP tool + contract.
2. **WU4 — `save_all` writes the wrong root tag.** `XmlTodoRepository.save_all` builds `ET.Element('TODO', ...)` while the format (and `analyze_structure`) is `TODOLIST`. Round-trips through the tooling hide it, but the real ToDoList app would reject the file. Options: (a) fix to `TODOLIST` and add a round-trip regression test, (b) leave and log as a separate defect.
3. **WU6 — nested markdown rendering lost.** The legacy `format_tasks_as_markdown` recursed with 2-space indent; the new `src/tools.py` markdown loops only render top-level tasks. `TestFormatTasksAsMarkdown::test_nested_children` has no target. Options: (a) extract a recursive formatter and restore nesting, (b) encode the reduced behaviour as expected.

## Known intentional divergences (encoded in migrated tests)
- `_decode_date` returns `date | None` (was ISO string / original string).
- `_encode_date` takes `date|datetime|None` (None → `""`).
- `Priority.from_str("3")` → `Priority.URGENT` (legacy mapped "3" → "High").
- `_hex_to_bgr` returns `int` (was string).
- `_find_task_by_pos("", …)` → `None` (legacy returned the root element).
- `_find_parent_of_task` returns the parent `Task` or `None` (legacy returned the root for top-level).
