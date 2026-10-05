# AI Review API

FastAPI service: `POST /review` takes `{"diff": "..."}`, sends it to an LLM and
returns `{"review": "..."}`. The LLM is the local Ollama model `itmo-agent`.
Python 3.14, FastAPI, pytest. No UI yet.

## Read first

| What | Where |
|---|---|
| Contract, features A/B, status | `docs/requirements.md` — the source of truth |
| Code style rules | `docs/style-guide.md` — read before changing code, if it exists |
| Endpoint | `app/api.py` |
| LLM clients (`ReviewLLM` protocol, `OllamaLLM`) | `app/llm.py` |
| Test example | `tests/test_example.py` |
| Fake LLM and fixtures (`client`, `fake_llm`) | `tests/conftest.py` |

If the request and `docs/requirements.md` disagree, stop and ask. Do not guess.

## Commands

All commands run from this folder (`practices/practice_04/ai-review`).

```sh
sh scripts/check.sh                                  # the only accepted check
.venv/bin/python -m pytest tests/test_x.py -q        # one file, while iterating
.venv/bin/uvicorn app.api:app --reload               # manual run, needs Ollama
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # setup
```

Work is done only when `sh scripts/check.sh` passes. Paste its real output;
never claim a result you did not run.

## Workflow

1. Read the relevant section of `docs/requirements.md` and restate the
   acceptance criteria in one or two lines.
2. Load the matching skill:
   - `test-driven-development` for any backend feature or bugfix. Also read
     its `writing-good-tests.md`.
   - `frontend-design` for any UI, HTML or CSS work.
   - `webapp-testing` to check a UI in a real browser (Playwright). Run its
     `scripts/with_server.py --help` first. Start the app with
     `.venv/bin/uvicorn app.api:app --port 8000`. Save screenshots outside the repo.
     Playwright is not installed; ask before installing it.
3. Library questions (FastAPI, Pydantic, httpx, pytest): look up the docs
   through the Context7 MCP instead of answering from memory.
4. Red: write one failing test, run it, show the failure.
5. Green: write the smallest change that makes it pass.
6. Run `sh scripts/check.sh`, then report (see below).

## Testing rules

- Test behavior through HTTP using the `client` fixture, not internal functions.
- Tests never call a real LLM. Use `fake_llm`. To check that the LLM was *not*
  called, assert `fake_llm.calls == []`.
- Simulate LLM failures with a fake that raises, set through
  `app.dependency_overrides[get_llm]`. Do not sleep in tests.
- Cover the boundaries the contract names, such as exactly 20 000 vs 20 001 characters.

## Code rules

- Keep the endpoint thin. The LLM stays behind `ReviewLLM` and is injected
  with `Depends(get_llm)`.
- Error responses use `HTTPException` with the exact `detail` text from the
  contract. Never leak exception text or tracebacks to the client.
- Use type hints. Follow the existing naming. No new frameworks or layers for a small change.

## Frontend (if asked)

There is no UI yet. If a task asks for one:
- Load `frontend-design` first and show the short design plan before code.
- Prefer a single static page served by FastAPI. Ask before adding Node, a
  bundler or a framework.
- The page talks only to `POST /review` and shows the contract's error
  messages (413, 422, 502, 504) in plain language.

## Boundaries

- **Never** change `docs/requirements.md`, `scripts/check.sh`, `pytest.ini` or
  `.opencode/` unless the task says so.
- **Never** weaken, skip or delete a test to get green.
- **Never** commit, push or run `git reset`/`git checkout -- .`. The human
  reviews the diff and commits.
- **Never** read or print secrets (`.env`, API keys, the root `opencode.json`).
- **Ask first** before adding a dependency, editing files outside this folder,
  or making a change larger than the feature needs.

## Report format

At the end of a task, reply with:
1. What changed: files and one line each.
2. Commands you ran, with the failing output (red) and the passing output (green).
3. Anything left open, or a deviation from the contract.
