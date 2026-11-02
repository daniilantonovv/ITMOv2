# Real browser verification — 2026-11-01

Browser: Codex in-app browser; actual UI operations through CUA/Playwright locators. No Playwright dependency was installed in the project. Service: 127.0.0.1:8015 with three explicitly synthetic test collections; optional fault proxy: 8016. Production data/ untouched.

| Scenario | Expected | Observed |
|---|---|---|
| Uppercase Cyrillic, Enter | Two breakfast cards | “Тест: Завтрак в дорогу”, “Тест: Завтрак на двоих” |
| Category Завтраки AND query | One matching card | “Тест: Завтрак на двоих” |
| Open result | Existing receipt, totals, cart controls | Dialog showed own selected collection and existing controls |
| Clear search | Empty input, same category | Завтраки remained selected, its card remained |
| Nonexistent query | No cards, useful empty state | “Ничего не найдено. Измените запрос или категорию.” |
| Forced listing 503 | Clear cards, keep query, offer retry | Query “ЗАВТРАК” retained; “Повторить” shown |
| Retry after clearing fault | Same search succeeds | Two breakfast cards returned |
| Delayed old success | Latest УЖИН remains after old ЗАВТРАК completes | Only “Тест: Ужин дома”, empty status |
| Delayed old 503 | Latest УЖИН remains after old failure completes | Only “Тест: Ужин дома”, no error replacement |
| 1280px desktop viewport | Two result cards, no overflow | clientWidth=1280, scrollWidth=1280; screenshot checked |
| Keyboard receipt | Search Enter, card Enter, dialog Escape | Correct receipt opened and closed; focus returned to result card |
| 390px mobile viewport | No horizontal overflow; usable controls | clientWidth=390, scrollWidth=390, search controls fit and wrap; screenshot checked |

Screenshots: [desktop](search-desktop.png), [mobile](search-mobile.png). Fault proxy and replay instructions: [quickstart](../specs/001-collection-search/quickstart.md).

The receipt dialog was opened via the real card control. External cart links were inspected but not followed; no real purchase was made. Keyboard search/open/close was also exercised separately. Clipboard behavior was not separately exercised in this run; existing tests cover unchanged dashboard serving behavior. Manual browser checks are recorded observations, not an automated browser suite.

Browser console error log after the final workflow: empty.

## Unicode boundary found during final QA

Original HTML maxlength=120 blocked the 61st typed emoji: 60 code points / 120 UTF-16 units. After replacing native maxlength with code-point validation, filling 119 emoji and typing the 120th succeeded; Enter returned the matching 120-code-point synthetic title. A 121-code-point query showed “Введите не больше 120 символов.” with validity.valid=false. Clear reset validity and normal Cyrillic search worked again. The extra boundary fixture was removed from the disposable demo afterwards.
