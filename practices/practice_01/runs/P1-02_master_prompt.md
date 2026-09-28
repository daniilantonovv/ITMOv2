# P1-02 — ответ с Master Prompt v1 (OpenCode, vsellm/openai/gpt-5, agent plan)

Вложения: `MASTER_PROMPT_v1.md` (= раздел «Master Prompt v1» в [`../prompts.md`](../prompts.md)) и `TRAINING_PR.diff`. Ответ сохранён без правок; JSON отформатирован для чтения.

```json
{
    "summary": "PR добавляет метод review в сервис и эндпоинт POST /api/reviews, который отправляет diff во внешний LLM и возвращает его ответ как \"comment\". Схема ответа и обработка входа не соответствуют правилам репозитория.",
    "risks": [
        {
            "file": "app/review_service.py",
            "line": 13,
            "evidence": "        prompt = f\"Review this pull request and find problems:\\n{diff}\"",
            "risk": "Diff отправляется во внешний LLM без удаления секретов, что нарушает SEC-1."
        },
        {
            "file": "app/review_service.py",
            "line": 15,
            "evidence": "        return {\"comment\": answer}",
            "risk": "Ответ сервиса не соответствует требуемому формату (summary, risks, checks), нарушение OUT-1."
        },
        {
            "file": "app/api.py",
            "line": 10,
            "evidence": "    return review_service.review(payload[\"diff\"])",
            "risk": "Нет проверки длины diff и возврата HTTP 413 для входа >20 000 символов, нарушение API-1."
        }
    ],
    "checks": [
        "POST /api/reviews с payload.diff=\"...token=abc123...\": использовать заглушку LLM, возвращающую полученный prompt; ожидаемо ответ содержит исходный \"token=abc123\", подтверждая нарушение SEC-1.",
        "POST /api/reviews с любым валидным diff: ожидаемо ответ JSON имеет только ключ \"comment\" и отсутствуют \"summary\", \"risks\", \"checks\" (нарушение OUT-1).",
        "POST /api/reviews с diff длиной 20 001 символ: ожидаемо сервис не возвращает 413 (получается 200/другой код), что подтверждает отсутствие проверки размера (нарушение API-1)."
    ]
}
```

UNKNOWN: Содержимое app/dependencies.py и реализация LLM (включая возможную редакцию секретов, таймаут 10s и логирование по OBS-1) не видны в diff; наличие обработки 413 вне эндпоинта также неизвестно.
