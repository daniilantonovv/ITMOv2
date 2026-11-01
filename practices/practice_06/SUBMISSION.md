# ДЗ 6 — сдача

| Критерий | Где смотреть |
|---|---|
| Модель угроз (2) | [THREAT_MODEL.md](THREAT_MODEL.md), Mermaid и STRIDE |
| Кастомный judge prompt (1) | [judge-system-prompt.md](judge-system-prompt.md) |
| Атаки до исправлений (2) | [REPORT_01.md](REPORT_01.md), [evidence/before](evidence/before/) |
| Исправления / checks (2) | [service.py](lab/service.py), [test_security.py](lab/test_security.py), [test_availability.py](lab/test_availability.py), make step6 и make test |
| Повторные атаки (2) | [REPORT_02.md](REPORT_02.md), [evidence/after](evidence/after/), [availability после](evidence/availability-after/) и [первая пара LLM](evidence/after-trial-01/) |
| PR и выводы (1) | [PR #5](https://github.com/daniilantonovv/ITMOv2/pull/5); текст [PR_BODY.md](PR_BODY.md) |

```sh
make step6  # 48 Mini Shop tests
make test
python3 practices/practice_06/lab/attacks.py /tmp/itmo-shop-replay
python3 practices/practice_06/lab/availability_probe.py /tmp/itmo-shop-availability.json
# Реальная LLM, установленный OpenCode и локальная Ollama:
python3 practices/practice_06/lab/evaluate_model.py /tmp/itmo-shop-replay
# Только replay уже сохранённых exact-ответов:
python3 practices/practice_06/lab/evaluate_model.py practices/practice_06/evidence/after-trial-01 --replay-only
```

`attacks.py` создаёт только собственный loopback-процесс и временный Sandbox. LLM-запуски сохраняют final-текст и метаданные, не reasoning. Зависимости Mini Shop: Python 3.10+ / stdlib; OpenCode/Ollama нужны только для необязательного повторного LLM-эксперимента. Исходные тесты и sandbox.py не ослаблялись. В unittest-логах удалены только пробелы в конце строк; final-ответы моделей сохранены дословно.

Выводы: исправление границ доступа важнее успешной атаки конкретной LLM. Реальная модель однажды выбрала export_profiles даже на обычном запросе; после фикса сервер не исполняет такое решение. Повторы показали и правильный чек, и ошибки формата: все результаты сохранены.

В отдельной принудительной проверке delete_tree сервер вернул 403 и сохранил чек. Это доказывает ограничение исполнителя, но не выдаётся за успешную prompt injection. Для такого стенда воспроизводимые HTTP-проверки и честный отчёт об ошибках модели полезнее заявлений об абсолютной безопасности.
