# Feature Specification: Collection title search

**Feature Branch**: `codex/homework-5-search`
**Created**: 2026-11-01
**Status**: Specified before implementation; final human review pending.
**Input**: User selected “Use collection search” for the existing VkusVill project.

## User Scenarios & Testing

### User Story 1 - Find a collection (Priority: P1)
As a dashboard visitor I can find a collection by part of its title, including Russian text, without inspecting every category.
**Why this priority**: The dashboard only shows ten collections although storage holds one hundred.
**Independent Test**: Search for an older matching title hidden beyond the latest ten, open its receipt.
**Acceptance Scenarios**:
1. Given “Завтрак на двоих”, when I submit “  ЗАВТРАК  ”, then its card appears.
2. Given more than ten newer nonmatches, when I search an older title, then that result appears.
3. Given “Сырники” only in products, when I search “Сырники”, then that collection is not a title match.

### User Story 2 - Combine and clear (Priority: P2)
As a visitor I combine a title query with a category and can clear only the query.
**Independent Test**: Search across two categories, choose one, clear, verify that category stays selected.
**Acceptance Scenarios**:
1. Category AND title are both applied; newest matching cards appear first.
2. Empty/whitespace q returns the previous list; clearing retains category.

### User Story 3 - Recover from no results and errors (Priority: P3)
As a visitor I get a useful message and a retry action, without stale cards replacing my latest search.
**Independent Test**: Submit a nonexistent title, retry a failed request, then complete two requests out of order.
**Acceptance Scenarios**:
1. An empty match says “Ничего не найдено. Измените запрос или категорию.”
2. A failed search clears cards, preserves controls and offers “Повторить”.
3. An older request completing late cannot change cards, status, categories or the hero.

### Edge Cases
120 raw Unicode code points accepted; 121 rejected with 422, including whitespace. %, _, quotes and SQL-looking input are literal. Cyrillic case folding is required. The empty database keeps its existing empty message when no filter is active.

## Requirements

- FR-001: GET /api/collections accepts optional q; trim and Unicode casefold, literal title substring only.
- FR-002: Validate raw q length <=120; apply category and q before newest-first limit (1–100, default 10).
- FR-003: Preserve the response schema and all other API endpoints; no data migration.
- FR-004: Labeled search form, Enter/“Найти”, clear button; existing category/details/cart controls work.
- FR-005: Latest request alone controls the list; expose loading, results, filtered-empty, empty-database and retry states.
- FR-006: Existing 503 detail stays “storage unavailable”; existing 422 validation format stays FastAPI's.

### Key Entities
CollectionSummary is unchanged: id, title, category, cart_url, created_at, totals, product_count. There is no total_count field and no products list in summaries.

## Success Criteria

- SC-001: All acceptance scenarios map to HTTP regression tests or recorded browser checks.
- SC-002: Existing 63 checks and new search checks pass through the trusted runner.
- SC-003: A visitor finds and opens a known collection using keyboard alone.

## Assumptions
The service's existing 100-row cap permits casefold filtering of a bounded set in Python. Search does not search product names, normalize diacritics, transliterate, paginate, or change category counts. Implementation choices are delegated by the user's request; these are not claimed as a separate human sign-off.
