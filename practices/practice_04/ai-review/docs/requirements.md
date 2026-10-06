# AI Review API — contract

`POST /review` accepts JSON `{"diff": "<unified diff>"}` and returns
`200 {"review": "<LLM answer>"}`.

## Feature A — input validation

| Input | Status | Body |
|---|---|---|
| `diff` is empty or whitespace only | 422 | FastAPI validation error |
| `diff` longer than 20 000 characters | 413 | `{"detail": "diff too large: max 20000 characters"}` |
| valid diff (1–20 000 characters) | 200 | `{"review": ...}` |

- A rejected request **must not call the LLM**.
- Exactly 20 000 characters is still valid (boundary).
- Note: Pydantic `max_length` returns 422, not 413, so it is not enough for the size check.

## Feature B — LLM dependency failure

- Waiting for the LLM is limited to `LLM_TIMEOUT_SECONDS` (default 30).
- On timeout: `504 {"detail": "LLM timeout"}`.
- On an unavailable LLM (connection error): `502 {"detail": "LLM unavailable"}`.
- Internal exception text and stack traces never reach the client.
- All Feature A scenarios keep working unchanged.

## Status

- [x] Feature A
- [x] Feature B
