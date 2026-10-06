"""The collections MCP server, called through the real MCP protocol (in-process client)."""

import httpx
import pytest
from fastapi.testclient import TestClient
from mcp import Client

from app.main import create_app
from mcp_server.server import build_server


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def api(tmp_path):
    return TestClient(create_app(db_path=tmp_path / "mcp.db"))


def collection(**overrides) -> dict:
    data = {
        "title": "Ужин за 20 минут",
        "category": "Ужины",
        "cart_url": "https://vkusvill.ru/cart/share/mcp-1",
        "products": [{"name": "Паста", "price": 129, "quantity": 2, "kcal": 350}],
        "operator_approved": True,
    }
    data.update(overrides)
    return data


async def call(http: httpx.Client, tool: str, args: dict):
    async with Client(build_server(http)) as client:
        return await client.call_tool(tool, args)


def text(result) -> str:
    return " ".join(block.text for block in result.content)


@pytest.mark.anyio
async def test_tools_are_listed(api):
    async with Client(build_server(api)) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}

    assert names == {"save_collection", "list_collections"}


@pytest.mark.anyio
async def test_approved_collection_is_saved_and_visible_in_api(api):
    result = await call(api, "save_collection", collection())

    assert not result.is_error
    saved = result.structured_content
    assert saved["title"] == "Ужин за 20 минут"
    assert saved["total_price"] == 258
    assert api.get(f"/api/collections/{saved['id']}").status_code == 200


@pytest.mark.anyio
async def test_not_approved_collection_is_not_saved(api):
    result = await call(api, "save_collection", collection(operator_approved=False))

    assert result.is_error
    assert "not approved" in text(result)
    assert api.get("/api/collections").json() == []


@pytest.mark.anyio
async def test_invalid_input_returns_readable_field_errors(api):
    bad = collection(cart_url="http://evil.example/cart", products=[{"name": "x", "price": -1}])

    result = await call(api, "save_collection", bad)

    assert result.is_error
    message = text(result)
    assert "cart_url" in message
    assert "products.0.price" in message
    assert api.get("/api/collections").json() == []


@pytest.mark.anyio
async def test_duplicate_cart_is_reported(api):
    await call(api, "save_collection", collection())

    result = await call(api, "save_collection", collection(title="Ещё раз"))

    assert result.is_error
    assert "already exists" in text(result)
    assert len(api.get("/api/collections").json()) == 1


@pytest.mark.anyio
async def test_service_down_is_reported_without_traceback():
    def refuse(request):
        raise httpx.ConnectError("connection refused", request=request)

    down = httpx.Client(base_url="http://127.0.0.1:8010", transport=httpx.MockTransport(refuse))

    result = await call(down, "save_collection", collection())

    assert result.is_error
    assert "not reachable" in text(result)
    assert "Traceback" not in text(result)


@pytest.mark.anyio
async def test_list_collections_returns_newest_first(api):
    await call(api, "save_collection", collection(title="Первая"))
    await call(api, "save_collection", collection(title="Вторая", cart_url="https://vkusvill.ru/cart/share/mcp-2"))

    result = await call(api, "list_collections", {"limit": 5})

    assert not result.is_error
    titles = [c["title"] for c in result.structured_content["collections"]]
    assert titles == ["Вторая", "Первая"]
