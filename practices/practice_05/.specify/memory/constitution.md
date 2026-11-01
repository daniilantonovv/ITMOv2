# VkusVill Collections feature constitution

Version 1.0.0; adopted 2026-11-01.

1. A UI specification and a logic specification share one explicit HTTP contract before application edits.
2. Extend the existing service in ../practice_04/vkusvill-collections. Keep its API summaries, SQLite schema, CRUD, cap, duplicate handling and storage error behavior.
3. No new application dependency, framework, build step, or invented product data. Use Python 3.14, FastAPI, sqlite3 and browser JavaScript already present.
4. Write meaningful failing HTTP tests, implement, then run the project's trusted scripts/check.sh. Check actual UI interactions separately.
5. Treat search strings as literal data; support Russian case folding; render API data with textContent. Async stale responses must not replace current results.
6. Save actual evidence. Model drafts are untrusted suggestions. Do not claim human acceptance, an independent review, or a browser run that did not happen.
