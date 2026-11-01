# Demo (about two minutes)

From the repository root:

```sh
make step5
make -C practices/practice_05 run
```

The second command opens a local service at http://127.0.0.1:8015. The SQLite file is disposable and all cards start with “Тест:”. Product values come from existing test fixtures, not a real VkusVill quote. Stop with Ctrl+C.

1. Type `ЗАВТРАК` into “Название подборки” and press Enter: two breakfast cards appear despite the uppercase input.
2. Choose “Завтраки”: one card remains. Open it with Enter to inspect the existing receipt/totals/cart controls, then close.
3. “Очистить” removes the query and retains “Завтраки”.
4. Search `Неттакойподборки`: no cards, clear recovery message.
5. HTTP boundary: `curl -G --data-urlencode 'q=ЗАВТРАК' http://127.0.0.1:8015/api/collections` returns the same two summaries.

Optional controlled failure/race demo, separate terminal:

```sh
python3 practices/practice_05/scripts/browser_proxy.py
```

Open http://127.0.0.1:8016. Write `{"fail":true}` to `/tmp/itmo-hw5-proxy.json`, submit a search and observe the error and “Повторить”. Replace the file with `{}`, click retry: same query succeeds. Write `{"delay_query":"ЗАВТРАК"}`, quickly submit ЗАВТРАК then УЖИН: only dinner stays after the four-second delayed response. Add `"fail_delayed":true` to check a late failure also cannot replace the current result. The proxy is test infrastructure, not part of the application.
