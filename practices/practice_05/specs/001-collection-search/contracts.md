# Shared UI / logic contract (version 1)

Final contract prepared before application edits. Both after-specifications reference this file.

`GET /api/collections?limit=10&category=<exact value>&q=<literal title substring>`

| Concern | Agreed behavior |
|---|---|
| q | Optional string, default empty; <=120 code points before trim; Python Unicode casefold |
| Scope | Only Collection.title; no product-name matching |
| Combination | category exact AND normalized title contains normalized q |
| Ordering | Filter all at-most-100 stored collections, newest id first, then limit |
| Success | 200, existing CollectionSummary[]; [] for zero matches |
| Validation | 422, existing FastAPI validation envelope; no storage mutation |
| Storage failure | 503, {"detail":"storage unavailable"} |
| Controls | Form submit/Enter triggers search; clear resets q and retains category |
| States | Loading, results, filtered-empty, original empty-database, error with retry |
| Concurrency | A monotonically increasing request number discards obsolete success AND failure |
| Compatibility | No query means existing behavior; category counts are global; details and cart actions unchanged |

Example: `q=ЗАВТРАК&category=Завтраки` matches title “Завтрак на двоих”, never a collection with “завтрак” only in a product name.

No new endpoint, response wrapper, total_count, authentication mechanism or database column.
