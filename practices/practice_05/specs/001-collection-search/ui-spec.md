# UI specification — reconciled

Source draft: [before/ui-spec.md](before/ui-spec.md). Authority: [contracts.md](contracts.md).

Put one search form immediately above the existing category chips: a visible label “Название подборки”, search input (placeholder “Например, завтрак”), “Найти” submit, and “Очистить” button. Onest, herb green, existing button/focus styles, mobile wrapping; no new animation. Enter submits. Validate <=120 Unicode code points (Array.from), not native maxlength UTF-16 units; explain an overlong query and clear custom validity on editing/clearing. A clear action returns focus to the input and keeps category selected.

Track submitted q separately from input text. Encode q/category with URLSearchParams. Use the existing summary[] cards and details, including totals/product_count. Do not invent total_count or read products from summaries.

Loading clears old cards and marks the list busy. Show the original empty message only when no category/query is active. Filtered-empty says “Ничего не найдено. Измените запрос или категорию.” Errors clear cards, retain query/category, and offer retry of the same submitted state. Keep category counts global. Only the most recent load can render results, errors or hero data; a late response is ignored.

Security: all user text uses textContent; no HTML highlighting. Accessible visible label, native buttons, role=status announcement, existing keyboard focus behavior.

Correction of the model draft: search -> q; title+products -> title only; null -> []; no total_count; API errors are 422/503, not an invented 400/500 schema.
