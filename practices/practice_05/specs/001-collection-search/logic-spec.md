# Logic specification — reconciled

Source draft: [before/logic-spec.md](before/logic-spec.md). Authority: [contracts.md](contracts.md).

Add q to the existing list route with Query(max_length=120). Pass it to CollectionStore.list. Keep category parameterized in SQLite, order by id descending; q.strip().casefold() is a literal substring of title.casefold(). Fetch matching category's bounded rows, filter before slicing to limit. No SQL LIKE (Cyrillic case folding and wildcard semantics would violate the contract).

A missing/empty/space-only q follows the old list behavior. Empty result is []. Invalid q returns 422 without writes. Existing storage failure maps to the same 503 handler. All models, category counts, database schema, CRUD, cart URL constraints, duplicate protection, totals and retention remain unchanged.

Correction of the model draft: response remains full CollectionSummary[], not collection_id/title; default limit is 10, max 100; Unicode is supported; title LIKE is replaced by literal Unicode casefold filtering.
