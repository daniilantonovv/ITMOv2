# Handoff — VkusVill Collections

State on 2026-11-01, submission branch `codex/homework-5-search` ([PR #6](https://github.com/daniilantonovv/ITMOv2/pull/6), final review pending).

## Done

| What | Where | Who |
|---|---|---|
| CRUD API, SQLite, 100-collection cap, categories | `app/`, `tests/test_collections_*.py` | written test-first before the practice |
| Dashboard (receipt, crates, КБЖУ) | `app/static/` | built with the `frontend-design` skill |
| Feature A: 409 on a duplicate `cart_url` | `app/storage.py` (UNIQUE index), `app/main.py` (handler) | OpenCode agent, TDD; revised after human review (race condition) |
| Feature B: 503 on storage failure | `app/storage.py` (`_db()`), `app/main.py` (handler) | OpenCode agent in worktree `practice-04-b`; review fixes by hand |
| Own MCP server `collections` (save_collection, list_collections) | `mcp_server/`, `tests/test_mcp_server.py` | Claude Code, homework 4 |
| Own skill `collection-approval` (preview + approval) | `.opencode/skills/collection-approval/` | Claude Code, homework 4 |
| Agent setup | `AGENTS.md`, `docs/style-guide.md`, `.opencode/` (3 skills, hook, `tester`), `opencode.json` (Context7) | |
| Homework 5: collection title search | `q` in list API/store, accessible search/clear, Unicode casefold, stale-response guard; `tests/test_collection_search.py` | Spec Kit artifacts in `../../practice_05/`; two independent UI/backend draft sessions |

## Sources of truth

- Contract and status: `docs/requirements.md`. A and B are done; the agent flow is not.
- Rules for agents: `AGENTS.md`. Code rules: `docs/style-guide.md`.

## How to check

```sh
sh scripts/check.sh            # verified: 80 passed (63 existing + 17 search cases)
.venv/bin/uvicorn app.main:create_app --factory --port 8010
```

The `check-after-edit` hook runs the same check after every agent edit
(`.opencode/hook.log` holds the event log).

## Known limits and open points

- Homework 3 and 4 have already been reviewed, as confirmed by the user on
  2026-11-01. Their GitHub PRs #4 and #3 are still open and unmerged as of
  this check. HW5 targets `practice_04` to keep its diff separate, not because
  HW4 is awaiting review.
- Homework 5 is implemented and checked, including a real browser; final human
  acceptance remains pending. The user explicitly authorized the submission PR
  on 2026-11-01, overriding the default no-commit rule for this submission. See
  `../../practice_05/README.md` from the project root. `make step5` in the repo
  root runs the trusted runner; `make -C practices/practice_05 run` serves a
  disposable synthetic demo. Title search filters before limit, uses Unicode
  code points for the 120-character boundary, and leaves category counts global.
- **Agent flow, half done:** the saving side exists (`collection-approval`
  skill + `collections` MCP, approval required). Fetching from the VkusVill MCP
  is not connected yet: we need its address and auth.
- **Model budget:** the VseLLM key returned `402` during stage 5. The
  `@explore` review of B and the `@tester` run did not happen. The review was
  done by a human; run `@tester` on B once the budget is back.
- OpenCode here is **1.18**, not 2.0 from the slides. The hook uses
  `tool.execute.after`, skills are listed by `opencode debug skill`, and there
  is no `opencode reload` (restart instead).
- An agent once ran a repo-wide `git diff` and printed the root key into its
  log (redacted in `homework/evidence`). The rule now allows only `git diff -- .`.
- The root `opencode.json` holds a literal API key and is excluded from git
  via `.git/info/exclude`. Never stage it.
- Feature A's storage-level test does not reproduce real concurrency. The
  guarantee is the UNIQUE index.
- Worktree `../ITMOv2-p4-b` (branch `practice-04-b`) is merged and can be
  removed with `git worktree remove ../ITMOv2-p4-b`.

## Next step for a new session

> Прочитай AGENTS.md и docs/HANDOFF.md. Что уже сделано и что осталось?
> Запусти проверку проекта. Пока ничего не меняй.
