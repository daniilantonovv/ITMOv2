# Unit-проверки

Объект — чистые функции конвейера из [`adr.md`](adr.md#решение): `redact()`, `ReviewRequest`, `validate_response()`. Без сети и без настоящего LLM.

| Требование или правило | Что проверяем изолированно | Вход | Ожидаемый результат | Evidence |
|---|---|---|---|---|
| U-01 · SEC-1 | `redact()` заменяет токены и ключи | `+token = "ghp_TEST0000000000000000000000000000000"`; `+AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`; блок `-----BEGIN PRIVATE KEY-----…` | Во всех трёх строках значение заменено на `[REDACTED]`, остальной текст строки сохранён | pytest `test_redact_known_formats` (параметризован по корпусу канареечных секретов) |
| U-02 · SEC-1 (ложные срабатывания) | `redact()` не портит обычный код | `+    prompt = f"Review this pull request..."` и `+def generate(self, prompt: str)` | Строки не изменены | pytest `test_redact_keeps_code` |
| U-03 · API-1 (граница) | Guard принимает ровно 20 000 символов | `diff = "a" * 20_000` | Проверка пройдена, исключения нет | pytest `test_size_limit_boundary` |
| U-04 · API-1 | Guard отклоняет 20 001 символ | `diff = "a" * 20_001` | `PayloadTooLarge` → HTTP 413 | pytest `test_size_limit_exceeded` |
| U-05 · OUT-1 | `validate_response()` принимает корректный ответ модели и режет лишние риски | JSON c `summary`, 4 рисками и `checks` | Результат соответствует `ReviewResponse`, `len(risks) == 3` | pytest `test_validate_trims_to_three` |
| U-06 · QA-1 | `validate_response()` отбрасывает риск без подтверждения | Риск с `evidence: "os.system(cmd)"`, которого нет в diff | Риск удалён, остальные сохранены | pytest `test_validate_drops_unbacked_risk` |
| U-07 · OUT-1 | Невалидный ответ модели | Текст `"Код можно улучшить"` вместо JSON | `InvalidModelOutput` (API → 502), исходный текст модели не попадает в исключение | pytest `test_validate_rejects_free_text` |
| U-08 · вход | `ReviewRequest` | `{}`, `{"diff": 123}` | `ValidationError` → 422 | pytest `test_request_schema` |
| U-09 · SEC-1 (идемпотентность) | Повторный `redact()` не меняет результат | Выход U-01 | `redact(redact(x)) == redact(x)` | pytest `test_redact_idempotent` |
| U-10 · SEC-1 / API-1 (скорость) | `redact()` на максимальном diff | `diff` 20 000 символов из смеси кода и 30 канареек | < 50 мс на CI-раннере | pytest-benchmark `test_redact_speed` |
| U-11 · REL-1 | Адаптер LLM превращает таймаут и ошибку провайдера в доменные исключения | `FakeClient`, который ждёт 15 с; `FakeClient`, который поднимает `ConnectionError` | `LLMTimeout` (API → 504) и `LLMUnavailable` (API → 503); текст ошибки провайдера не попадает в исключение | pytest `test_llm_adapter_maps_errors` (таймаут эмулируется, реальных 15 с не ждём) |

## Как использовали AI

- Строка в [`prompts.md`](prompts.md): P1-02 — `checks` из ответа модели стали основой U-01 и U-04; U-09 и U-10 добавлены по итогам Tree of Thoughts, U-11 — по итогам RAG-проверки покрытия ([`../practice_02/rag/experiment.md`](../practice_02/rag/experiment.md)): у REL-1 не было unit-проверки ([`../practice_02/prompts.md`](../practice_02/prompts.md) E2-04).
- Что проверили и исправили сами: проверка модели для SEC-1 использовала `token=abc123` — такой строки не поймает ни один реалистичный паттерн, заменили на корпус реальных форматов; добавили U-02 (ложные срабатывания) и U-03 (граница 20 000), которых модель не предложила; U-06 добавили после того, как модель в P1-02 сама указала неточные номера строк.
