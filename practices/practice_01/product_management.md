# Use cases и user stories

## Первый рабочий сценарий

**Когда** ревьюер отправляет diff одного PR в `POST /api/reviews`, **система** удаляет из него секреты, проверяет размер, за ≤ 10 с получает от LLM разбор и оставляет только риски, подтверждённые строкой diff, **а пользователь получает** JSON с `summary`, не более чем тремя рисками (`file`, `line`, `evidence`, `risk`) и списком воспроизводимых проверок.

Не входит в этот сценарий:

- публикация комментариев, approve/merge и любые действия в GitHub (SCOPE-1);
- автоматический запуск помощника из CI или GitHub App — ревьюер вызывает API сам;
- ревью нескольких PR сразу, разбиение большого diff на части (diff > 20 000 символов отклоняется);
- аутентификация, квоты, выбор LLM-провайдера.

## Use case

| Поле | Значение |
|---|---|
| Актор | Ревьюер backend-команды |
| Триггер | Ревьюеру назначен PR, он отправляет его diff в `POST /api/reviews` |
| Предусловия | Сервис запущен (`GET /health` → 200); настроен LLM-клиент с timeout 10 с; есть список паттернов секретов для SEC-1 |
| Основной результат | 200 и JSON по OUT-1: `summary`, `risks` (0–3, каждый с дословной строкой diff), `checks`; в prompt к LLM нет секретов; в логе только `request_id`, длительность, статус |
| Ошибка или отказ | `{}` или `diff` не строка → 422; diff > 20 000 символов → 413 без вызова LLM; LLM не ответил за 10 с → 504, ошибка провайдера → 503 — тело без содержимого diff; ответ LLM не проходит схему → риски без evidence отбрасываются, при полном провале → 502 «Не удалось получить разбор» |

```mermaid
sequenceDiagram
    actor User as Ревьюер
    participant API as API /api/reviews
    participant Svc as ReviewService
    participant AI as Внешний LLM
    User->>API: POST {"diff": "..."}
    API->>API: Схема ReviewRequest, len(diff) ≤ 20 000
    alt невалидный вход
        API-->>User: 422 / 413
    else ок
        API->>Svc: review(diff)
        Svc->>Svc: redact секретов → [REDACTED]
        Svc->>AI: Master prompt + размеченный diff (timeout 10 с)
        alt timeout / ошибка
            Svc-->>API: LLMUnavailable
            API-->>User: 504 / 503 без текста diff
        else ответ
            AI-->>Svc: JSON-предложение
            Svc->>Svc: схема OUT-1, evidence ∈ diff, risks ≤ 3
            Svc-->>API: ReviewResponse
            API-->>User: 200 {summary, risks, checks}
        end
    end
    Note over User: Решение по PR принимает ревьюер (SCOPE-1)
```

## User stories и acceptance criteria

- **US-1.** Как ревьюер, я хочу получать до трёх рисков PR с файлом, строкой и цитатой, чтобы проверить каждый за секунды, а не искать его в diff.
- **US-2.** Как инженер по безопасности, я хочу, чтобы секреты из diff никогда не попадали во внешний LLM, чтобы ревью не создавало утечек.
- **US-3.** Как ревьюер, я хочу получать понятную ошибку за ≤ 12 с, если LLM недоступен или diff слишком большой, чтобы не ждать бесконечно и знать, что делать дальше.
- **US-4.** Как владелец сервиса, я хочу, чтобы в логах не было содержимого diff и ответа модели, чтобы логи можно было хранить и читать без допуска к коду.

```gherkin
Feature: Структурированный разбор PR для ревьюера (US-1)

  Scenario: Позитивный — риски подтверждены строками diff
    Given сервис запущен и подставной LLM возвращает валидный JSON с 2 рисками
    And evidence каждого риска дословно содержится в отправленном diff
    When ревьюер отправляет POST /api/reviews с diff из TRAINING_PR.diff
    Then статус ответа 200
    And ответ содержит поля summary, risks и checks
    And в risks не больше 3 элементов, у каждого есть file, line, evidence, risk

  Scenario: Граничный — модель вернула риск без подтверждения
    Given подставной LLM возвращает 4 риска, у одного evidence нет в diff
    When ревьюер отправляет POST /api/reviews с этим diff
    Then статус ответа 200
    And риск с неподтверждённым evidence отсутствует в ответе
    And в risks не больше 3 элементов

Feature: Защита секретов (US-2)

  Scenario: Негативный — diff содержит токен
    Given diff содержит строку "+GITHUB_TOKEN = 'ghp_TEST0000000000000000000000000000000'"
    When ревьюер отправляет POST /api/reviews с этим diff
    Then prompt, переданный в LLM, содержит "[REDACTED]"
    And prompt не содержит подстроку "ghp_TEST"

  Scenario: Негативный — пароль в строке подключения к БД
    Given diff содержит строку "+DATABASE_URL = 'postgres://user:passw0rd@db.internal:5432/appdb'"
    When ревьюер отправляет POST /api/reviews с этим diff
    Then prompt, переданный в LLM, содержит "[REDACTED]"
    And prompt не содержит подстроку "passw0rd"

  Scenario: Негативный — многострочный приватный ключ PEM
    Given diff содержит блок:
      """
      +-----BEGIN PRIVATE KEY-----
      +MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
      +MzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu
      +NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ
      +-----END PRIVATE KEY-----
      """
    When ревьюер отправляет POST /api/reviews с этим diff
    Then prompt, переданный в LLM, содержит "[REDACTED]"
    And prompt не содержит ни одну из строк тела ключа, включая последнюю "NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ"

  Scenario: Граничный — секрет в удалённой строке diff
    Given diff содержит строку "-PASSWORD = 'SuperSecret123!'"
    When ревьюер отправляет POST /api/reviews с этим diff
    Then prompt, переданный в LLM, не содержит подстроку "SuperSecret123!"

  Scenario: Граничный — слово token в обычном коде не редактируется
    Given diff содержит строку "+print('access token expired')"
    When ревьюер отправляет POST /api/reviews с этим diff
    Then prompt, переданный в LLM, содержит "access token expired"
    And prompt не содержит "[REDACTED]"

Feature: Контролируемые отказы (US-3)

  Scenario: Негативный — пустое тело
    When ревьюер отправляет POST /api/reviews с телом {}
    Then статус ответа 422
    And LLM не вызывается

  Scenario: Граничный — размер diff
    When ревьюер отправляет diff длиной 20 000 символов
    Then статус ответа 200
    When ревьюер отправляет diff длиной 20 001 символ
    Then статус ответа 413
    And LLM не вызывается

  Scenario: Негативный — LLM не отвечает
    Given подставной LLM отвечает через 15 секунд
    When ревьюер отправляет POST /api/reviews
    Then статус ответа 504 не позже чем через 11 секунд
    And тело ответа не содержит текст diff

  Scenario: Негативный — провайдер LLM вернул ошибку
    Given подставной LLM поднимает ConnectionError
    When ревьюер отправляет POST /api/reviews
    Then статус ответа 503
    And тело ответа не содержит текст diff и текст ошибки провайдера

Feature: Логи без содержимого (US-4)

  Scenario: Позитивный — в логе только метаданные
    When ревьюер отправляет POST /api/reviews с diff, содержащим маркер "CANARY-42"
    Then запись в логе содержит request_id, duration_ms и status
    And лог не содержит "CANARY-42"
```

## Как использовали AI

- Для чего: получить черновик user stories и Gherkin по Context Pack (P1-03); расширить критерии US-2 примерами (Few-shot, Практика 2, E2-01).
- Тип промпта: master prompt (P1-03); few-shot (E2-01).
- Строка в [`prompts.md`](prompts.md): P1-03; [`../practice_02/prompts.md`](../practice_02/prompts.md) E2-01.
- Что проверили и исправили сами: из P1-03 взяли 4 истории (ревьюер, безопасность, SRE-ограничения) и сценарии 413 / ровно 20 000 / timeout. Исправили: пример секрета `token=abcd1234` заменили на реалистичные форматы; при timeout модель предлагала отдавать ответ OUT-1 — мы выбрали 504/503 (ADR-001), REL-1 допускает оба варианта; добавили отсутствовавший сценарий `{}` → 422 и сценарий отбрасывания неподтверждённого риска (QA-1). В Few-shot отклонили проверку «нет `BEGIN PRIVATE KEY`» — заголовок не секрет.
