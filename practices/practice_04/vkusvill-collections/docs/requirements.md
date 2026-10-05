# VkusVill Collections — contract

A public dashboard of themed product collections ("подборки"). An operator asks
an agent to build a collection with the VkusVill MCP. After the operator
explicitly approves it, the agent saves the collection to this service. The
dashboard shows it.

MVP. Developed test-first.

## Data model

`Collection` (input):

| Field | Type | Rules |
|---|---|---|
| `title` | string | 1–120 characters after trimming |
| `category` | string | 1–50 characters after trimming; set at creation, used for grouping |
| `cart_url` | string | `https://` URL on `vkusvill.ru` or a subdomain of it |
| `products` | list of `Product` | 1–100 items |

`Product`:

| Field | Type | Rules |
|---|---|---|
| `name` | string | 1–200 characters |
| `price` | number | rubles per unit, `>= 0` |
| `quantity` | integer | `>= 1`, default `1` |
| `kcal`, `protein`, `fat`, `carbs` | number | per unit, `>= 0`, default `0` |

`Collection` (output) adds:

- `id`: integer, assigned by the server.
- `created_at`: ISO 8601 UTC.
- `totals`: `{price, kcal, protein, fat, carbs}`, the sums of `value * quantity`
  over all products, each rounded to 2 decimals.

## API

All endpoints are under `/api`. Errors are JSON `{"detail": ...}`.

| Method & path | Success | Notes |
|---|---|---|
| `POST /api/collections` | 201 + collection | |
| `GET /api/collections` | 200 + list of summaries | newest first; `?limit=` 1–100, default 10; `?category=` exact filter |
| `GET /api/collections/{id}` | 200 + collection | 404 if missing |
| `PUT /api/collections/{id}` | 200 + collection | full replace; keeps `id` and `created_at`; 404 if missing |
| `DELETE /api/collections/{id}` | 204 | 404 if missing |
| `GET /api/categories` | 200 + `[{category, count}]` | sorted by category name |

A summary is a collection without `products`, plus `product_count`.

Invalid input returns 422. A missing collection returns 404 `{"detail": "collection not found"}`.

## Storage

- SQLite. The file path comes from `COLLECTIONS_DB` (default `data/collections.db`).
- Keep at most **100** collections. Creating the 101st deletes the oldest one.

## Dashboard

Served at `GET /`. A static page that uses only the API above.

- Shows the 10 most recent collections as cards with a mock image, title,
  category, product count and total price.
- Can filter by category, using `GET /api/categories`.
- Clicking a card opens the details: a product list with quantity and price,
  the total price, total КБЖУ, a "copy cart link" button and an "open cart in
  VkusVill" link (new tab).
- Shows a clear empty state and a clear error state.

## Agent flow (not in this step)

The agent gets products and a cart link from the VkusVill MCP. It shows them
to the operator and calls `POST /api/collections` **only after explicit
approval**.

## Status

- [x] CRUD API
- [x] 100-collection cap
- [x] Dashboard
- [ ] Agent flow
