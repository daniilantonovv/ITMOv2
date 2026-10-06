# ДЗ 4 — сдача

Точка входа: **[index.html](index.html)** (блоки А–Г с подтверждениями).
Рефлексия: [reflection.md](reflection.md). Логи и выводы: [evidence/](evidence/).

| Блок | Где в проекте `../vkusvill-collections` |
|---|---|
| А. Среда | `AGENTS.md`, `docs/style-guide.md`, `.opencode/` (skills, plugin, agents), `opencode.json` |
| Б. Свой skill | `.opencode/skills/collection-approval/` + `tests/test_skill_preview.py` |
| В. Свой MCP | `mcp_server/server.py` + `tests/test_mcp_server.py`, демо `scripts/mcp_demo.py` |

Проверка: `cd ../vkusvill-collections && sh scripts/check.sh` → 63 passed.
