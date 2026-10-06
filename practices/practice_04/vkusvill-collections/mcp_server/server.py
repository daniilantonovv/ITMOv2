"""MCP server for the VkusVill Collections service.

Lets an agent save a collection it built with the VkusVill MCP into this
service, but only after the operator approved it, and read what is stored.
It talks to the service over its public HTTP API (`/api`), so the API stays
the single place for validation.

Run (stdio): .venv/bin/python -m mcp_server.server
Service URL: COLLECTIONS_API_URL (default http://127.0.0.1:8010).
"""

import os

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

DEFAULT_API_URL = "http://127.0.0.1:8010"
TIMEOUT_SECONDS = 10.0


class ProductIn(BaseModel):
    """One product line as returned by the VkusVill MCP. Values are per unit."""

    name: str
    price: float = Field(description="Price in rubles per unit")
    quantity: int = 1
    kcal: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class SavedCollection(BaseModel):
    id: int
    title: str
    category: str
    product_count: int
    total_price: float
    url: str = Field(description="API link to the saved collection")


class CollectionList(BaseModel):
    collections: list[dict]


def _field_errors(body: dict) -> str:
    """Turn FastAPI 422 details into 'products.0.price: Input should be ...'."""
    parts = []
    for error in body.get("detail", []):
        location = ".".join(str(p) for p in error.get("loc", []) if p != "body")
        parts.append(f"{location}: {error.get('msg', 'invalid')}")
    return "; ".join(parts) or "invalid input"


def _request(http: httpx.Client, method: str, path: str, **kwargs) -> httpx.Response:
    try:
        return http.request(method, path, **kwargs)
    except httpx.TimeoutException as error:
        raise ToolError(f"The collections service did not answer in {TIMEOUT_SECONDS:g}s. Try again later.") from error
    except httpx.HTTPError as error:
        raise ToolError(
            f"The collections service is not reachable at {http.base_url}. "
            "Start it with: .venv/bin/uvicorn app.main:create_app --factory --port 8010"
        ) from error


def build_server(http: httpx.Client) -> MCPServer:
    server = MCPServer(
        "vkusvill-collections",
        instructions=(
            "Saves product collections to the VkusVill Collections dashboard. "
            "Always show the collection to the operator first and call save_collection "
            "with operator_approved=true only after an explicit yes."
        ),
    )

    @server.tool()
    def save_collection(
        title: str,
        category: str,
        cart_url: str,
        products: list[ProductIn],
        operator_approved: bool,
    ) -> SavedCollection:
        """Save an approved product collection to the dashboard.

        Call this only after the operator has seen the title, category, products
        with prices and the cart link, and explicitly said yes. Use only data
        returned by the VkusVill MCP; never invent prices or links.
        cart_url must be an https link on vkusvill.ru.
        """
        if not operator_approved:
            raise ToolError(
                "Not saved: the operator has not approved this collection. "
                "Show it to the operator and ask for an explicit yes first."
            )
        payload = {
            "title": title,
            "category": category,
            "cart_url": cart_url,
            "products": [p.model_dump() for p in products],
        }
        response = _request(http, "POST", "/api/collections", json=payload)
        if response.status_code == 201:
            body = response.json()
            return SavedCollection(
                id=body["id"],
                title=body["title"],
                category=body["category"],
                product_count=len(body["products"]),
                total_price=body["totals"]["price"],
                url=str(http.base_url.join(f"/api/collections/{body['id']}")),
            )
        if response.status_code == 409:
            raise ToolError("Not saved: a collection with this cart_url already exists.")
        if response.status_code == 422:
            raise ToolError(f"Not saved: invalid input. {_field_errors(response.json())}")
        if response.status_code == 503:
            raise ToolError("Not saved: the service storage is unavailable. Try again later.")
        raise ToolError(f"Not saved: unexpected response {response.status_code} from the service.")

    @server.tool()
    def list_collections(limit: int = 10, category: str | None = None) -> CollectionList:
        """List saved collections, newest first (limit 1–100, optional exact category).

        Use it to check whether a collection is already saved before asking the operator.
        """
        params: dict = {"limit": limit}
        if category:
            params["category"] = category
        response = _request(http, "GET", "/api/collections", params=params)
        if response.status_code == 422:
            raise ToolError(f"Invalid query. {_field_errors(response.json())}")
        if response.status_code != 200:
            raise ToolError(f"The service answered {response.status_code}. Try again later.")
        return CollectionList(collections=response.json())

    return server


def main() -> None:
    base_url = os.environ.get("COLLECTIONS_API_URL", DEFAULT_API_URL)
    with httpx.Client(base_url=base_url, timeout=TIMEOUT_SECONDS) as http:
        build_server(http).run("stdio")


if __name__ == "__main__":
    main()
