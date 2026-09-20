# P1-05 — прогон Master Prompt v2

> **Исполнитель — не OpenCode.** 20.09.2026 шлюз VseLLM (`litellm.data-light.ru`) обрывал TLS-соединение, прогнать v2 на `vsellm/openai/gpt-5` не удалось. Промпт выполнен агентом Claude Opus 5 (Claude Code) по тому же контракту: вход — только `TRAINING_PR.diff` и текст Master Prompt v2, без доступа к остальным артефактам. Это делает P1-05 проверкой переносимости промпта на другую модель, а не повтором P1-04 на той же.

Вход: [«Master Prompt v2»](../prompts.md#master-prompt-v2) + [`TRAINING_PR.diff`](../TRAINING_PR.diff).

```json
{
  "summary": "PR добавляет ReviewService.review(), который отправляет diff во внешний LLM и возвращает его ответ, и эндпоинт POST /api/reviews, принимающий тело запроса как произвольный dict.",
  "risks": [
    {
      "file": "app/review_service.py",
      "line": 14,
      "evidence": "prompt = f\"Review this pull request and find problems:\\n{diff}\"",
      "risk": "Diff подставляется в prompt как есть, без удаления токенов, паролей и приватных ключей: любой секрет из PR уходит внешнему провайдеру. Нарушает SEC-1."
    },
    {
      "file": "app/review_service.py",
      "line": 15,
      "evidence": "answer = self.llm.generate(prompt)",
      "risk": "Вызов внешнего LLM без таймаута и обработки ошибок: при зависании провайдера запрос висит неограниченно, ошибка уходит наружу неконтролируемо. Нарушает REL-1 (timeout 10 секунд, контролируемый ответ)."
    },
    {
      "file": "app/review_service.py",
      "line": 16,
      "evidence": "return {\"comment\": answer}",
      "risk": "Ответ сервиса — свободный текст модели в поле comment, без summary, risks и checks с полями file, line, evidence, risk. Нарушает OUT-1, и клиент не может отличить подтверждённый риск от выдуманного."
    }
  ],
  "checks": [
    "SEC-1: подменить llm на заглушку, сохраняющую полученный prompt; отправить POST /api/reviews с diff, где есть строка +GITHUB_TOKEN = 'ghp_TEST0000000000000000000000000000000'. Ожидаемо после исправления: в сохранённом prompt есть [REDACTED] и нет подстроки ghp_TEST. Сейчас: токен присутствует в prompt дословно.",
    "REL-1: заглушка llm.generate спит 15 секунд. Ожидаемо после исправления: запрос завершается не позже 11 секунд контролируемым ответом. Сейчас: запрос висит до таймаута клиента.",
    "OUT-1: заглушка llm.generate возвращает строку 'ok'; отправить валидный diff. Ожидаемо после исправления: тело ответа содержит ключи summary, risks, checks. Сейчас: тело содержит единственный ключ comment."
  ]
}
```

UNKNOWN: проверка длины diff и ответ 413 по API-1 в diff не видны — они могли быть реализованы в middleware или в отсутствующем в diff `app/dependencies.py`; там же может находиться timeout внутри клиента LLM. Логирование по OBS-1 в изменённом коде не затрагивается, его текущее состояние по diff не определить.
