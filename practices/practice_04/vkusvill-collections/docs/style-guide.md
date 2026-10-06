# Style guide

Five rules for this service. Each one has a real example in the code.

1. **Test behavior through HTTP.** Use the `client` fixture and assert on
   status, body and what is stored, not on internal functions.
   Example: `tests/test_feature_a_no_duplicate_carts.py::test_post_duplicate_cart_url_returns_409`.

2. **Guarantees live in the database, not in check-then-write code.**
   Uniqueness, limits and other invariants go into SQL (constraints, one
   statement, one transaction).
   Example: `idx_collections_cart_url` in `app/storage.py`.

3. **Storage raises domain errors; one handler maps each to HTTP.**
   Routes don't catch errors themselves. The client gets only the contract
   text, never SQLite messages.
   Example: `DuplicateCartUrlError` → `handle_duplicate_cart_url` in `app/main.py`.

4. **Use the stack we have.** FastAPI, Pydantic, stdlib `sqlite3`, plain JS.
   No ORM, framework or build step for a small change.

5. **Never weaken the runner to get green.** `scripts/check.sh`, `pytest.ini`
   and existing tests change only when the task says so.

## Good example

```python
# app/storage.py: the database enforces the rule; storage translates the error.
except sqlite3.IntegrityError as e:
    if "cart_url" in str(e):
        raise DuplicateCartUrlError(f"cart_url {data.cart_url} already exists")
    raise

# app/main.py: one place turns the domain error into the contract response.
@app.exception_handler(DuplicateCartUrlError)
def handle_duplicate_cart_url(request, exc):
    return JSONResponse(status_code=409, content={"detail": "collection with this cart_url already exists"})
```
