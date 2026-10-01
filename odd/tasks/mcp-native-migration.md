# Feature: MCP Native Migration (pi-mcp-adapter -> Pi core)

**Status**: Done (pending restart verification)
**Goal**: Move all MCP servers from the `pi-mcp-adapter` extension to Pi-native MCP support (Pi 0.99.x), so Pi can manage the servers itself and Codemode applies.

## Problem Statement
Pi 0.99.0 moved MCP into the core (Codemode + lazy tool loading + native lifecycle). Keep using the adapter means the servers stay under the extension's control and native features do not apply. The adapter also owned the live status-bar indicator, which is the reason the migration changes the UI.

## Tasks
- [x] Inventory the currently registered servers (`mcp-adapter.json`).
- [x] Confirm the native `mcp.json` schema and field mapping against the Pi docs (`docs/mcp.md`).
- [x] Back up the adapter config.
- [x] Write the native `mcp.json` with all 6 servers.
- [x] Neutralize the adapter config to avoid double-loading.
- [x] Verify end-to-end with `pi mcp list`.
- [ ] Restart Pi (full process) and re-verify the loaded servers.

## Servers Migrated
| Server | Transport | Exposure | Tools |
| --- | --- | --- | --- |
| codegraph | stdio (`codegraph serve --mcp`) | codemode (default) | 1 |
| context-mode | stdio (`node .../context-mode/cli.bundle.mjs`) | codemode (default) | 11 |
| engram | stdio (`node -e ...`) | codemode | 19 |
| hound | http (`http://192.168.1.62:8765/mcp`) | codemode (default) | 6 |
| todolist | stdio (`venv python.exe main.py`, cwd `K:/todolist_mcp`) | codemode (default) | 17 |
| github | http (`https://api.githubcopilot.com/mcp/`) | hidden + 9 direct | 25 |

## Field Mapping (adapter -> native)
- Dropped adapter-only fields: `lifecycle`, `httpTransport`, `protocolVersion`, `auth`, `bearerToken`, `directTools`, `includeTools`.
- `directTools: false` -> `exposure: "codemode"` (also the native default).
- `directTools: true` + `includeTools` (9) -> `exposure: "hidden"` + `toolExposure: {<tool>: "direct"}`.
- `bearerToken: "!gh auth token"` -> header `"Authorization": "!echo Bearer $(gh auth token)"` (native supports `!command` in env/header values).
- Note: native disables a server with `enabled: false`, not the adapter's `disabled: true`.

## Evidence
- `pi mcp list` -> exit 0; all 6 servers connected with the tool counts above.
- Files: `~/.pi/agent/mcp.json` (new), `~/.pi/agent/mcp-adapter.json` (now `{"mcpServers": {}}`).
- Backup: `~/.pi/agent/mcp-adapter.json.bak-20261001-171327` (original, 1852 bytes).

## UI Impact (known, tracked upstream)
- The live status bar loses `🔌 MCP: N servers enabled (M connected)`: that text is painted by `pi-mcp-adapter` (`formatMcpFooterStatus`), not by Pi. Upstream issue #688, no PR yet.
- The gentle-pi startup banner now reads `~/.pi/agent/mcp.json` and will show `MCP: 6 server(s)` (issue #979; fix in unmerged PR #980).

## Revert
```bash
cd ~/.pi/agent && cp mcp-adapter.json.bak-20261001-171327 mcp-adapter.json && rm mcp.json
```

## Follow-ups
- [ ] Restart Pi and verify `/mcp`.
- [ ] Investigate a local fix for the status indicator (gentle-pi shell-bar / banner reading native Pi MCP state).
- [ ] Consider reporting #688 / opening a PR.
- [ ] Decide whether to remove `npm:pi-mcp-adapter` from `~/.pi/agent/settings.json` packages.
