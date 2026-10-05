# VkusVill Collections

Public dashboard of themed VkusVill product collections, plus a CRUD API.
An operator builds collections with an agent and the VkusVill MCP. After
explicit approval the agent saves them here. MVP, developed test-first.
Python 3.14, FastAPI, SQLite (stdlib `sqlite3`), static HTML/CSS/JS.

## Read first

| What | Where |
|---|---|
| Contract: model, API, limits, dashboard, status | `docs/requirements.md` — the source of truth |
| Current state, open points | `docs/HANDOFF.md` |
| Code style rules | `docs/style-guide.md` — **read before changing code** |
| App factory and routes | `app/main.py` (`create_app(db_path)`) |
| Pydantic models, validation, totals | `app/models.py` |
| SQLite storage and the 100-row cap | `app/storage.py` (`CollectionStore`) |
| Dashboard | `app/static/index.html`, `styles.css`, `app.js` |
| Test fixtures (`client`, `new_collection`) | `tests/conftest.py` |

If the request and `docs/requirements.md` disagree, stop and ask. Do not guess.

## Commands

All commands run from this folder (`practices/practice_04/vkusvill-collections`).

```sh
sh scripts/check.sh                                            # the only accepted check
.venv/bin/python -m pytest tests/test_x.py -q                  # one file, while iterating
.venv/bin/uvicorn app.main:create_app --factory --port 8010    # run, open http://localhost:8010
.venv/bin/python scripts/seed.py                               # add 11 demo collections
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # setup
```

The database is `data/collections.db`; `COLLECTIONS_DB` overrides it.
`data/` is git-ignored. Work is done only when `sh scripts/check.sh` passes.
Paste its real output. A hook (`.opencode/plugins/check-after-edit.js`) also runs it
after every edit and appends `[check-after-edit] PASS/FAIL` to the tool result.
React to a FAIL before moving on.

## Workflow

1. Read the relevant section of `docs/requirements.md` and restate the
   acceptance criteria in one or two lines.
2. Load the matching skill:
   - `test-driven-development` for any API or storage change. Also read its
     `writing-good-tests.md`.
   - `frontend-design` for any dashboard UI, HTML or CSS work. Keep the
     existing design language in `styles.css`:
     - herb green, sage and price-label yellow;
     - Onest for the UI, IBM Plex Mono only on receipts;
     - the receipt-print animation is the page's single autoplaying motion,
       so don't add more;
     - the crate and barcode art is generated deterministically in `app.js`.
   - `webapp-testing` to check the dashboard in a real browser. Playwright is
     not installed; ask before installing it.
3. Library questions (FastAPI, Pydantic, sqlite3, pytest): look up the docs
   through the Context7 MCP.
4. Red: write one failing test, run it, show the failure. Green: make the
   smallest change. Then run `sh scripts/check.sh`.

## Testing rules

- Test through HTTP with the `client` fixture. It uses a fresh SQLite file in
  `tmp_path`, so never touch `data/`.
- Build payloads with `new_collection(**overrides)`. Do not copy JSON around.
- Every validation rule in the contract gets a parametrized case in
  `tests/test_collections_limits.py`, including that nothing was stored.

## Code rules

- Routes stay thin. Validation lives in `app/models.py` and SQL in `app/storage.py`.
- Totals are always computed from products (`Totals.of`), never stored.
- `cart_url` must stay restricted to `https` on `vkusvill.ru` or its subdomains,
  because the dashboard turns it into a link.
- Dashboard JS sets user data only with `textContent`. Never use `innerHTML`
  with API data.
- UI copy is in Russian, plain and specific. Errors say what happened and what to do.

## Saving collections from the VkusVill MCP

- Show the operator the title, category, products with prices and the cart
  link **before** saving.
- Call `POST /api/collections` only after an explicit "yes" in chat. No
  approval means nothing is saved.
- Never invent prices, nutrition or cart links. Use only what the MCP returned.

## Boundaries

- **Never** change `docs/requirements.md`, `scripts/check.sh`, `pytest.ini` or
  `.opencode/` unless the task says so.
- **Never** weaken, skip or delete a test to get green.
- **Never** commit, push or run destructive git commands. The human reviews and commits.
- **Never** read or print secrets (`.env`, API keys, the root `opencode.json`,
  MCP credentials).
- **Ask first** before adding a dependency, a framework or a build step, or
  before editing files outside this folder.

## Subagents

- `@tester` checks a finished feature against the contract (read-only).
- `@explore` reviews a diff for problems (read-only).

## Report format

1. What changed: files and one line each.
2. Commands you ran, with the red and green output.
3. Anything left open, or a deviation from the contract.
