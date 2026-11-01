# ДЗ 5 — две команды, одна фича

Фича: поиск подборок по названию в существующем **VkusVill Collections**. Пользователь выбрал collection search в чате. Реализация остаётся в [проекте ДЗ 4](../practice_04/vkusvill-collections); здесь находятся SDD-артефакты и сдача.

## Что сдаётся

| Критерий | Артефакт |
|---|---|
| Другой SDD-фреймворк (2) | Настоящий Spec Kit 1.2.5, .specify/, .opencode/commands/, [init evidence](evidence/speckit-init.txt), [constitution](.specify/memory/constitution.md) |
| Две спеки до/после и контракт (2) | [UI до](specs/001-collection-search/before/ui-spec.md), [логика до](specs/001-collection-search/before/logic-spec.md), [UI после](specs/001-collection-search/ui-spec.md), [логика после](specs/001-collection-search/logic-spec.md), [общий контракт](specs/001-collection-search/contracts.md), [согласование](specs/001-collection-search/reconciliation.md) |
| Реализация и сквозные проверки (5) | q в API/store, форма поиска, [17 HTTP cases](../practice_04/vkusvill-collections/tests/test_collection_search.py), [red](evidence/search-red.txt), [green](evidence/search-green.txt), [браузер](evidence/browser-checks.md) |
| Рефлексия (1) | [reflection.md](reflection.md) |

[Spec](specs/001-collection-search/spec.md), [plan](specs/001-collection-search/plan.md), [tasks](specs/001-collection-search/tasks.md), [демо на 2 минуты](specs/001-collection-search/quickstart.md).

## Воспроизведение

```sh
# Из корня репозитория, используя существующее окружение проекта:
make step5
make -C practices/practice_05 run
# http://127.0.0.1:8015 — только синтетические fixtures, временная SQLite
```

Если окружение ещё не настроено, используйте существующую команду из AGENTS проекта:

```sh
cd practices/practice_04/vkusvill-collections
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Фактический runner: `sh scripts/check.sh` → **80 passed** (63 прежних + 17 новых параметризованных случаев). До реализации новые тесты дали 14 failed / 3 passed. Отдельно проверены ошибки, задержанные ответы и мобильная ширина в настоящем браузере. Перед PR проверки повторены в отдельном checkout: [trusted runner](evidence/pr-check.txt) и [make test](evidence/pr-make-test.txt). В CLI/pytest-логах удалены только пробелы в конце строк; ответы моделей сохранены дословно.

## Как применён Spec Kit

Официальный источник: [github/spec-kit v1.2.5](https://github.com/github/spec-kit/tree/v1.2.5), [core CLI](https://github.github.io/spec-kit/reference/core.html). CLI установлен во временный /tmp/itmo-speckit-venv из официального Git-тега; это не новая зависимость сервиса. `specify init --here --integration opencode --script sh --ignore-agent-tools --force` создал реальную инфраструктуру. Спецификация начата из spec-template; setup-plan.sh создал plan, затем агент заполнил его. check-prerequisites.sh проверил spec/plan/tasks; результат сохранён в [evidence](evidence/speckit-prerequisites.json).

Две независимые OpenCode-сессии, `ui-spec` и `logic-spec`, получили отдельные [запросы](evidence/) и не имели инструментов. Сохраняются их реальные final-ответы, включая ошибки; исходники приложения ещё не менялись. До реализации составлены две исправленные спеки и общий контракт; hashes исходников сохранены в pre-implementation.json. Это эмуляция двух команд, а не две реальные команды людей.

## Сравнение с OpenSpec из практики

| Аспект | OpenSpec в материалах практики | Применённый Spec Kit |
|---|---|---|
| Единица работы | Изменение: proposal / specs / design / tasks, затем sync/archive | Feature spec, constitution, plan, tasks |
| Постоянные правила | rules в openspec/config.yaml | .specify/memory/constitution.md |
| Главный эффект здесь | Отдельно делает видимыми рамки изменения существующего проекта | Заставляет связать пользовательские сценарии, общий контракт и порядок реализации |
| Проверка CLI | Структура артефактов, не правильность поведения | Проверка наличия prerequisites, не семантики или безопасности |
| Цена процесса | Для маленькой фичи достаточно узкого change | Больше scaffolding; оставить компактные spec/plan/tasks и не раздувать сервис |

Человек выбрал фичу. Технические расхождения исправлял агент в рамках поручения. Финальная приёмка человеком ещё не заявлена и не подменяется зелёными тестами. Никакой OpenSpec archive не имитировался.
