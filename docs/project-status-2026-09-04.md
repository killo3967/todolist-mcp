# Informe de Estado del Proyecto

**Proyecto:** TodoList MCP Server
**Ruta:** `K:\todolist_mcp`
**Fecha del informe:** 2026-09-04
**Rama:** `master`

---

## 1. Resumen

Servidor MCP en Python para gestionar ficheros `.tdl` de [ToDoList](https://abstractspoon.com/), probado con **ToDoList 9.2.4**. Es un fork mejorado del proyecto original de [ispyridis/todolist-mcp](https://github.com/ispyridis/todolist-mcp).

| Característica | Valor |
|---|---|
| Herramientas MCP | **16** (las 11 originales + `complete_task`, `get_task_stats`, `backup_tdl`, `restore_tdl`, `delete_task`, `add_comment`) |
| Arquitectura | Modular: `src/models.py`, `src/manager.py`, `src/tools.py` |
| Entradas | `main.py` (principal), `tdl_mcp_server.py` (retrocompatibilidad) |
| Tests | **192** (80 unit en `test/` + 112 contract MCP en `test-contract/`) |
| Calidad | mypy + ruff + pyright limpio (según release v1.0.0) |
| Documentación | Diataxis en `docs/diataxis/` (tutorial, how-to, explanation, reference) |

---

## 2. Estado Git

| Item | Estado |
|---|---|
| Rama | `master` |
| Último commit | `b343222 release: v1.0.0` (2026-07-30) |
| Push | ⚠️ **1 commit sin pushear** a `origin/master` → la release **v1.0.0 no está publicada** |
| Tags | **Ninguno** creado |
| Cambios sin commitear | `src/tools.py` (ver §3) |
| Archivos sin trackear | 3 (ver §4) |

---

## 3. ⚠️ Cambio sin commitear — `src/tools.py`

Modificado el 2026-09-04. Contiene un intento a medias de **migración `MCPServer` → `FastMCP`**, además de la limpieza de **51 líneas muertas** (declaraciones pydantic `Field(...)` sobrantes del refactor).

### 3.1 Problema

- `requirements.txt` fija `mcp>=2.0.0` y el venv tiene **mcp 2.0.0**.
- En mcp **2.0.0 la clase `FastMCP` ya no existe**: la API moderna usa `MCPServer` (la que emplea el commit v1.0.0). `FastMCP` pertenece a mcp ≤1.x.
- Consecuencia: `from mcp.server import FastMCP` lanza `ImportError: cannot import name 'FastMCP'`.

### 3.2 Impacto

| Estado | Tests |
|---|---|
| Working tree actual (FastMCP roto) | **86 passed, 106 errors** (todos los contract que lanzan `main.py` como subproceso fallan con `RuntimeError: Server closed stdout unexpectedly`) |
| HEAD (v1.0.0, `MCPServer`) | Importa y arranca correctamente |

### 3.3 Caminos posibles (no ejecutados)

1. **Revertir** `src/tools.py` a HEAD → suite verde, coherente con mcp 2.0.0 instalado.
2. **Completar el port a FastMCP** → bajar `mcp` a 1.x en `requirements.txt`, adaptar la firma de las tools al API FastMCP y revalidar los 192 tests. Cambia la dependencia base del proyecto.
3. **Dejar el working tree tal cual** (decisión tomada: solo informe).

---

## 4. Archivos sin trackear

| Archivo | Origen | Observación |
|---|---|---|
| `docs/todolist-screenshot.png` (5.3 KB) | 2026-07-30 | Captura para documentación (válido) |
| `settings_debug_copy.json` | 2026-09-03 | **Basura** — copia de settings de Pi (investigación de plugins) |
| `uni_check.json` | 2026-09-04 | **Basura** — salida de chequeo de paquetes de Pi |

Los dos JSON de debug no pertenecen al proyecto; candidatos a borrar o añadir a `.gitignore`.

---

## 5. Configuración

Resolución del fichero `.tdl` (por prioridad):

1. `$TODOLIST_FILE` — variable de entorno (la fija el cliente MCP)
2. `mcp_server.ini` — fichero local con toggle `active = yes/no`
3. `~/todolist.tdl` — fallback por defecto

---

## 6. Próximos pasos pendientes (recomendados)

1. **Decidir** el destino del cambio de `src/tools.py` (§3.3). Mientras no se resuelva, el servidor no arranca.
2. **Pushear** `master` y crear el tag `v1.0.0` — release pendiente desde el 2026-07-30.
3. **Limpiar** `settings_debug_copy.json` y `uni_check.json`.
