# Ответ модели без правок

OpenCode 1.18.29, `vsellm/openai/gpt-5`, agent `plan`. Запрос — в [`experiment.md`](experiment.md).



| Утверждение | Вопрос | Источник (цитата) | Результат: подтверждено / опровергнуто / не проверяемо по diff |
|---|---|---|---|
| app/api.py:8–10 — добавлен POST /api/reviews; тело запроса payload: dict; в сервис передаётся payload["diff"] без проверки | Какие строки новой версии app/api.py реализуют POST /api/reviews и передают payload["diff"] без валидации? | app/api.py:8 `@app.post("/api/reviews")`<br>app/api.py:9 `def create_review(payload: dict) -> dict[str, str]:`<br>app/api.py:10 `return review_service.review(payload["diff"])` | подтверждено |
| app/review_service.py:13–16 — review() подставляет diff в prompt через f-string и возвращает {"comment": answer} | Какие строки новой версии app/review_service.py показывают f-string с diff и возврат {"comment": answer}? | app/review_service.py:13 `def review(self, diff: str) -> dict[str, str]:`<br>app/review_service.py:14 `prompt = f"Review this pull request and find problems:\n{diff}"`<br>app/review_service.py:15 `answer = self.llm.generate(prompt)`<br>app/review_service.py:16 `return {"comment": answer}` | подтверждено |
| app/api.py:3 — review_service импортируется из app.dependencies; содержимого этого модуля в diff нет | Какая строка импортирует review_service, и какие файлы вообще изменены в diff? | app/api.py:3 `from app.dependencies import review_service`<br>TRAINING_PR.diff заголовки файлов: `diff --git a/app/review_service.py b/app/review_service.py` и `diff --git a/app/api.py b/app/api.py` | подтверждено |
| SEC-1: перед отправкой во внешний LLM из diff удаляются токены, пароли и приватные ключи | Как сформулирован SEC-1 в CASE.md? | CASE.md:64 `SEC-1: перед отправкой во внешний LLM из diff удаляются токены, пароли и приватные ключи.` | подтверждено |
| API-1: diff длиннее 20 000 символов отклоняется с HTTP 413 | Как сформулирован API-1 в CASE.md? | CASE.md:65 `API-1: diff длиннее 20 000 символов отклоняется с HTTP 413.` | подтверждено |
| REL-1: внешний LLM-вызов имеет timeout 10 секунд; ошибка превращается в контролируемый ответ | Как сформулирован REL-1 в CASE.md? | CASE.md:66 `REL-1: внешний LLM-вызов имеет timeout 10 секунд; ошибка превращается в контролируемый ответ.` | подтверждено |
| OUT-1: ответ содержит summary, массив risks (≤3, с полями) и массив checks | Как сформулирован OUT-1 в CASE.md? | CASE.md:67 `OUT-1: ответ содержит summary, массив risks и массив checks. В risks максимум три элемента с полями file, line, evidence, risk.` | подтверждено |
| SCOPE-1: сервис только советует; он не пишет код и не выполняет действия в GitHub | Где это указано в CASE.md? | CASE.md:68 `SCOPE-1: сервис только советует; он не пишет код и не выполняет действия в GitHub.` | подтверждено |
| QA-1: риск включается только если подтверждён строкой diff или правилом | Где это указано в CASE.md? | CASE.md:69 `QA-1: риск включается в ответ, только если он подтверждён строкой diff или правилом репозитория.` | подтверждено |
| OBS-1: в лог пишутся только request_id, длительность и статус; содержимое diff и ответа модели не логируется | Где это указано в CASE.md? | CASE.md:70–71 `OBS-1: в лог пишутся только request_id, длительность и статус. Содержимое diff и ответа модели не логируется.` | подтверждено |
| Вход: метод и путь — POST /api/reviews | Какая строка новой версии app/api.py содержит декоратор POST /api/reviews? | app/api.py:8 `@app.post("/api/reviews")` | подтверждено |
| Вход: ожидается ключ "diff" в JSON | Какая строка новой версии app/api.py содержит обращение к payload["diff"]? | app/api.py:10 `return review_service.review(payload["diff"])` | подтверждено |
| Вход: diff — строка | Какая строка объявляет тип параметра diff как str? | app/review_service.py:13 `def review(self, diff: str) -> dict[str, str]:` | подтверждено |
| Вход: ограничение длины diff ≤ 20 000 символов | Какое правило задаёт лимит 20 000 и статус 413? | CASE.md:65 `API-1: diff длиннее 20 000 символов отклоняется с HTTP 413.` | подтверждено |
| Результат (OUT-1): summary, risks, checks (см. поля) | Где в CASE.md задан формат результата? | CASE.md:67 `OUT-1: ответ содержит summary, массив risks и массив checks. В risks максимум три элемента с полями file, line, evidence, risk.` | подтверждено |
| Ошибки: 413 — diff > 20 000 символов | Где это указано? | CASE.md:65 `API-1: diff длиннее 20 000 символов отклоняется с HTTP 413.` | подтверждено |
| Ошибки: 422 — нет поля "diff" или не строка | Где в diff или CASE.md указана выдача 422 при отсутствии/неверном типе diff? | — | не проверяемо по diff |
| Ошибки: 504/503 — LLM не ответил за 10 с или вернул ошибку; контролируемое тело без текста diff | Где в diff или CASE.md указаны статусы 504/503 и требование «без текста diff» в теле? | CASE.md:66 подтверждает только timeout 10 с и «контролируемый ответ»; статусы 504/503 и «без текста diff» не указаны | не проверяемо по diff |

Исправления:
- Раздел «Формат входа и результата» → пункт «Ошибки»: оставить только подтверждённые источниками факты. Предлагаю заменить на:
  - 413 — diff > 20 000 символов (API-1).
  - При таймауте/ошибке внешнего LLM (10 секунд) — контролируемый ответ (REL-1).
  Убрать неподтверждённые: 422 за отсутствующий/нестроковый diff; статусы 504/503; формулировку «без текста diff».
