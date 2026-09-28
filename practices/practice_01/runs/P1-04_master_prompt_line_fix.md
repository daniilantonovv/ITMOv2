# P1-04 — Master Prompt v1 + правило нумерации строк (OpenCode, vsellm/openai/gpt-5, agent plan)

Вложения: `MASTER_PROMPT_v1.md`, `TRAINING_PR.diff`. Запрос — в [`../prompts.md`](../prompts.md). Ответ без правок, JSON отформатирован.

```json
{
    "summary": "PR добавляет метод review в ReviewService и эндпоинт POST /api/reviews, которые отправляют содержимое diff во внешний LLM и возвращают результат как comment. Также изменено форматирование сигнатуры LLM.generate.",
    "risks": [
        {
            "file": "app/review_service.py",
            "line": 14,
            "evidence": "+        prompt = f\"Review this pull request and find problems:\\n{diff}\"",
            "risk": "Дифф отправляется во внешний LLM без удаления секретов (SEC-1), возможна утечка токенов/паролей/ключей."
        },
        {
            "file": "app/review_service.py",
            "line": 16,
            "evidence": "+        return {\"comment\": answer}",
            "risk": "Ответ сервиса не соответствует OUT-1 (нет summary/risks/checks), нарушен контракт формата ответа."
        },
        {
            "file": "app/review_service.py",
            "line": 15,
            "evidence": "+        answer = self.llm.generate(prompt)",
            "risk": "Вызов внешнего LLM без явного таймаута 10 секунд и обработки ошибок нарушает REL-1; возможны зависания и неконтролируемые ошибки."
        }
    ],
    "checks": [
        "POST /api/reviews с payload {\"diff\":\"token=TEST\"}; замокать llm.generate для возврата полученного prompt → ожидается, что в prompt вместо токена будет [REDACTED] (SEC-1).",
        "POST /api/reviews с payload {\"diff\":\"x\"}; llm.generate возвращает \"ok\" → ожидается JSON-ответ с полями summary, risks, checks (OUT-1).",
        "Симулировать llm.generate с задержкой 15 секунд → ожидается, что сервис прерывает вызов через 10 секунд и возвращает контролируемый ответ (REL-1)."
    ]
}
```

UNKNOWN: фильтрация секретов вне показанного кода; реализация таймаута и обработка ошибок внутри llm.generate; проверка длины diff и возврат 413 на других слоях; логирование по OBS-1
