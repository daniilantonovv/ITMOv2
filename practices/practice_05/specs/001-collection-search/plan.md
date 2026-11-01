# Implementation Plan: Collection title search

Branch codex/homework-5-search; 2026-11-01; [spec.md](spec.md).

## Summary
Extend the existing list route/store and dashboard with literal Unicode title search. No new service or dependency.

## Technical Context
Python 3.14, existing FastAPI/Pydantic, stdlib sqlite3, plain JS/CSS/HTML. SQLite file unchanged. At most 100 collections. pytest through existing scripts/check.sh; actual browser checks separately.

## Constitution Check
Shared contract and reconciled specs exist before app edits. Baseline 63 passed. Raw query length checked at HTTP boundary; parameterized category SQL; textContent; latest response guard; no new dependency. Human review is reported honestly as pending.

## Project Structure
Implementation: ../../practice_04/vkusvill-collections/app/{main.py,storage.py,static/*} and tests/test_collection_search.py.
Artifacts: spec.md, ui-spec.md, logic-spec.md, contracts.md, reconciliation.md, tasks.md, quickstart.md.

## Design
Bounded Python filtering avoids SQLite's ASCII-only default case handling. Apply the category WHERE clause, order by id DESC, normalize q, filter titles, then slice. UI submits explicitly, so no debounce library is needed. A request counter makes out-of-order completion harmless.

```mermaid
sequenceDiagram
    actor Visitor
    participant UI as Search form
    participant API as GET /api/collections
    participant Store as SQLite + bounded Unicode filter
    Visitor->>UI: Submit q and choose category
    UI->>API: q, category, limit=10
    API->>Store: Validate; list(q, category, limit)
    Store-->>API: Filtered newest summaries
    API-->>UI: 200 summary[] / 422 / 503
    UI-->>Visitor: Latest request's cards or recovery state
```

## Validation
Red HTTP tests before implementation; trusted runner after. Browser: Cyrillic search, Enter, category AND query, details, clear retaining category, zero matches, retry, and out-of-order replies. Keep database fixtures temporary and do not seed real product data.
