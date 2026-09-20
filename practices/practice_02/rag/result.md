# Ответ модели без правок

OpenCode 1.18.29, `vsellm/openai/gpt-5`, agent `plan`. Запрос — в [`experiment.md`](experiment.md).



| Правило | Unit | Integration | E2E | Load | Пробел |
|---|---|---|---|---|---|
| [CASE.md#SEC-1] | [tests_unit.md#U-01], [tests_unit.md#U-02] | [tests_integration.md#INT-04] | [tests_e2e.md#E2E-04] |  | Load — нет в источниках |
| [CASE.md#API-1] | [tests_unit.md#U-03], [tests_unit.md#U-04] | [tests_integration.md#INT-05] | [tests_e2e.md#E2E-03] | [tests_load.md#L-03] |  |
| [CASE.md#REL-1] |  | [tests_integration.md#INT-02] |  | [tests_load.md#L-02] | Unit, E2E — нет в источниках |
| [CASE.md#OUT-1] | [tests_unit.md#U-05], [tests_unit.md#U-07] | [tests_integration.md#INT-01] | [tests_e2e.md#E2E-01] |  | Load — нет в источниках |
| [CASE.md#SCOPE-1] |  |  |  |  | Unit, Integration, E2E, Load — нет в источниках |
| [CASE.md#QA-1] | [tests_unit.md#U-06] | [tests_integration.md#INT-03] | [tests_e2e.md#E2E-01] |  | Load — нет в источниках |
| [CASE.md#OBS-1] |  | [tests_integration.md#INT-04] | [tests_e2e.md#E2E-02], [tests_e2e.md#E2E-04] | [tests_load.md#L-01] | Частично: под нагрузкой не проверено отсутствие diff/ответа в логах [CASE.md#OBS-1] |

Предлагаемые проверки для пробелов
1. REL-1: добавить E2E негативный сценарий с задержкой/ошибкой провайдера, ожидать 504 ≤ 11 с и 503 при ошибке, без текста diff в теле [CASE.md#REL-1].
2. SEC-1, OBS-1: добавить нагрузочный сценарий с канареечными секретами в diff; проверять, что в prompt только [REDACTED] и в логах сервиса нет секретов [CASE.md#SEC-1], [CASE.md#OBS-1].
3. SCOPE-1: добавить интеграционную/E2E-проверку, что сервис не выполняет действий вне «советовать» (нет побочных эффектов вроде GitHub-операций) [CASE.md#SCOPE-1].
