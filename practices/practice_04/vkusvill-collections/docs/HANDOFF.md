# Handoff — VkusVill Collections

State on 2026-10-05, branch `practice_04`, commit `b9c1bb1`.

## Done

| What | Where | Who |
|---|---|---|
| CRUD API, SQLite, 100-collection cap, categories | `app/`, `tests/test_collections_*.py` | written test-first before the practice |
| Dashboard (receipt, crates, КБЖУ) | `app/static/` | built with the `frontend-design` skill |
| Feature A: 409 on a duplicate `cart_url` | `app/storage.py` (UNIQUE index), `app/main.py` (handler) | OpenCode agent, TDD; revised after human review (race condition) |
| Feature B: 503 on storage failure | `app/storage.py` (`_db()`), `app/main.py` (handler) | OpenCode agent in worktree `practice-04-b`; review fixes by hand |
| Agent setup | `AGENTS.md`, `docs/style-guide.md`, `.opencode/` (3 skills, hook, `tester`), `opencode.json` (Context7) | |

## Sources of truth

- Contract and status: `docs/requirements.md`. A and B are done; the agent flow is not.
- Rules for agents: `AGENTS.md`. Code rules: `docs/style-guide.md`.

## How to check

```sh
sh scripts/check.sh            # expected: 52 passed
.venv/bin/uvicorn app.main:create_app --factory --port 8010
```

The `check-after-edit` hook runs the same check after every agent edit
(`.opencode/hook.log` holds the event log).

## Known limits and open points

- **Agent flow is not built.** We need the VkusVill MCP address and its auth.
  The rule is already in `AGENTS.md`: save only after explicit approval.
- **Model budget:** the VseLLM key returned `402` during stage 5. The
  `@explore` review of B and the `@tester` run did not happen. The review was
  done by a human; run `@tester` on B once the budget is back.
- OpenCode here is **1.18**, not 2.0 from the slides. The hook uses
  `tool.execute.after`, skills are listed by `opencode debug skill`, and there
  is no `opencode reload` (restart instead).
- The root `opencode.json` holds a literal API key and is excluded from git
  via `.git/info/exclude`. Never stage it.
- Feature A's storage-level test does not reproduce real concurrency. The
  guarantee is the UNIQUE index.
- Worktree `../ITMOv2-p4-b` (branch `practice-04-b`) is merged and can be
  removed with `git worktree remove ../ITMOv2-p4-b`.

## Next step for a new session

> Прочитай AGENTS.md и docs/HANDOFF.md. Что уже сделано и что осталось?
> Запусти проверку проекта. Пока ничего не меняй.
