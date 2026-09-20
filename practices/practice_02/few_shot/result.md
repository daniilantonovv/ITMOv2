# Few-shot — ответ модели без правок

OpenCode 1.18.29, `vsellm/openai/gpt-5`, agent `plan`. Запрос — в [`experiment.md`](experiment.md#запрос).

```gherkin
Scenario: Пароль в строке подключения к БД (URL)
  Given diff содержит строку "+DATABASE_URL = 'postgres://user:passw0rd@db.internal:5432/appdb'"
  When ревьюер отправляет POST /api/reviews с этим diff
  Then prompt, переданный в LLM, содержит "[REDACTED]"
  And prompt не содержит подстроку "passw0rd"

Scenario: Приватный ключ PEM из нескольких строк
  Given diff содержит блок:
    """
    +-----BEGIN PRIVATE KEY-----
    +MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
    +abc123abc123abc123abc123abc123ab
    +xyz987xyz987xyz987xyz987xyz987xy
    +-----END PRIVATE KEY-----
    """
  When ревьюер отправляет POST /api/reviews с этим diff
  Then prompt, переданный в LLM, содержит "[REDACTED]"
  And prompt не содержит подстроку "BEGIN PRIVATE KEY"

Scenario: Ложное срабатывание — слово token в обычном коде не редактируется
  Given diff содержит строку "+print('access token expired')"
  When ревьюер отправляет POST /api/reviews с этим diff
  Then prompt, переданный в LLM, содержит "access token expired"
  And prompt не содержит "[REDACTED]"

Scenario: Секрет в удалённой строке diff (начинается с "-")
  Given diff содержит строку "-PASSWORD = 'SuperSecret123!'"
  When ревьюер отправляет POST /api/reviews с этим diff
  Then prompt, переданный в LLM, содержит "[REDACTED]"
  And prompt не содержит подстроку "SuperSecret123!"
```
