# Two-team reconciliation before code

Two fresh OpenCode sessions (`ui-spec` and `logic-spec`) used the same local ollama/itmo-agent model, with tools denied and no shared chat history. Requests are in ../../evidence; exact final model drafts are retained in before/. No internal reasoning is retained.

| Draft mismatch / error | Resolution in both after-specifications |
|---|---|
| UI search vs backend q | q on the existing endpoint |
| UI title + products vs backend title | title only; smaller useful feature selected by implementing agent |
| UI total_count / missing totals; backend collection_id/title | unchanged CollectionSummary[] |
| UI null / 400/500 vs existing service | [] / FastAPI 422 / existing 503 |
| Backend LIKE despite Unicode and literal requirements | bounded Python casefold substring |
| Limit ambiguity | filter before limit, newest id first |
| Neither draft handles async stale replies clearly | request sequence guards success, failure and hero |

User explicitly selected collection search. Narrow technical choices above were resolved under the request to implement homework. No claim is made that the user separately reviewed these drafts or that the final implementation has human acceptance. The reviewable contract is contracts.md. SHA-256 of application files before implementation is in evidence/pre-implementation.json.
