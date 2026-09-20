# P1-01 — ответ zero-shot (OpenCode, vsellm/openai/gpt-5, agent plan)

Запрос: `Ниже diff учебного PR. Посмотри PR и найди проблемы.` + вложение `TRAINING_PR.diff`. Ответ сохранён без правок.

Findings

Critical
- app/api.py:36-38 – Missing input validation. Accessing payload["diff"] without schema or presence checks will raise KeyError and return 500 for malformed requests. Use a Pydantic model to validate required fields and produce 422 responses.
- app/review_service.py:19-22 and app/api.py:36-38 – Unbounded input size. Passing an arbitrary diff directly into the LLM can blow past context limits, cause excessive latency/cost, or crash upstream clients. There’s no truncation, chunking, or guardrails.
- app/api.py:36-38 – No error handling around LLM call path. Any exception from review_service.review/llm.generate will bubble up as 500. Wrap with proper exception handling and map to meaningful HTTP errors/timeouts.

High
- app/api.py:36-38 – Weak typing for request/response. Using plain dict for the request body and dict[str, str] for the response yields poor OpenAPI docs and no field-level validation. Define Pydantic models for input/output.
- app/review_service.py:19-22 – Layering/design leakage. Service returns a transport-friendly dict; this couples domain logic to API shape. Prefer returning a domain value (e.g., a string or a small dataclass) and let the API adapt it to JSON.
- app/api.py:36-38 – Sync endpoint calling potentially slow IO. If llm.generate does network IO, a sync def relies on the threadpool and can block workers under load. Consider making the endpoint async and using an async LLM client or running the call in a dedicated executor/background task.
- app/api.py:36-38 – No auth/authorization. Anyone can POST diffs and consume LLM capacity. Add auth or rate limiting if this is exposed beyond trusted environments.

Medium
- app/review_service.py:19-22 – Prompt injection/exfiltration risk. The raw diff is interpolated directly into the prompt; adversarial diffs can steer the model. Add system/user role separation and prompt hardening, and consider sanitizing or delimiting user content clearly.
- app/review_service.py:19-22 – No output normalization. The LLM output is returned verbatim. Downstream renderers may need formatting or safety checks (e.g., ensuring text-only output if rendered in HTML to avoid XSS on a client).
- app/api.py:36-38 – Missing response_model annotation. Without an explicit response_model, OpenAPI will show a generic object and validation of responses is skipped.
- app/review_service.py:10-13 – typing.Protocol availability depends on Python version. Using Protocol from typing and dict[str, str] requires Python ≥3.9 (Protocol is in typing in 3.8+, but dict[...] needs 3.9). If you target 3.8, use typing_extensions.Protocol and typing.Dict[str, str].

Low
- app/review_service.py:10-13 – Style-only change from one-line stub to multiline ellipsis; not harmful, but unnecessary churn.
- Overall – Lack of tests. No unit test for ReviewService with a fake LLM, and no API test for POST /api/reviews happy path and error cases.
- app/api.py – Naming. create_review is fine, but consider aligning with domain naming (e.g., review_pull_request) for clarity.

Open Questions
- What Python version is the project targeting in production? This impacts use of dict[str, str] and typing.Protocol.
- Is the LLM client synchronous or async? Do we have timeout/retry/circuit-breaker behavior defined?
- Expected maximum diff size? Do we need chunking/summarization strategy and token budgeting?
- Is this endpoint intended to be public or internal-only? Do we need auth/rate limits?
- What is the desired response structure? Single comment string or a structured set of findings with severity, file/line references?

Change Summary (proposed)
- Introduce Pydantic models: ReviewRequest{diff: str}, ReviewResponse{comment: str}. Use these in the endpoint with response_model=ReviewResponse.
- Validate and guard input size. Enforce a max diff length; for larger diffs, summarize, chunk, or reject with 413.
- Add error handling and timeouts around llm.generate. Map to 4xx/5xx appropriately; log failures with correlation IDs.
- Adjust layering: make ReviewService.review return a string or structured domain object; let the API shape JSON.
- Consider async endpoint and an async LLM client or move the call to a background task if it’s long-running.
- Harden prompt construction: clearly delimit user diff, add a stable system prompt, and mitigate prompt injection patterns.
- Add basic tests: unit tests for ReviewService with a stub LLM, and FastAPI tests for POST /api/reviews covering valid, missing diff, oversized diff, and LLM exceptions.
