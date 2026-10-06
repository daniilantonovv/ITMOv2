"""Real MCP calls over stdio: start mcp_server the way OpenCode does and call its tools.

Usage: .venv/bin/python scripts/mcp_demo.py http://127.0.0.1:8012
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent

COLLECTION = {
    "title": "Ужин за 20 минут",
    "category": "Ужины",
    "cart_url": "https://vkusvill.ru/cart/share/mcp-demo-1",
    "products": [
        {"name": "Спагетти", "price": 129, "kcal": 1720, "protein": 60, "fat": 7, "carbs": 350},
        {"name": "Томаты в собственном соку", "price": 159, "kcal": 90, "protein": 4, "carbs": 16},
    ],
    "operator_approved": True,
}


def server(api_url: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=str(ROOT / ".venv/bin/python"),
        args=["-m", "mcp_server.server"],
        cwd=str(ROOT),
        env={"COLLECTIONS_API_URL": api_url},
    )


def show(step: str, result) -> None:
    print(f"\n### {step}")
    print(f"is_error: {result.is_error}")
    if result.structured_content and not result.is_error:
        print(json.dumps(result.structured_content, ensure_ascii=False, indent=2))
    else:
        print(" ".join(block.text for block in result.content))


async def main(api_url: str) -> None:
    async with Client(server(api_url)) as client:
        tools = (await client.list_tools()).tools
        print("### tools/list")
        for tool in tools:
            print(f"- {tool.name}: {tool.description.splitlines()[0]}")

        show("1. save_collection — approved, valid", await client.call_tool("save_collection", COLLECTION))
        show("2. save_collection — same cart again", await client.call_tool("save_collection", COLLECTION))
        show("3. save_collection — invalid input", await client.call_tool("save_collection", {
            **COLLECTION, "cart_url": "http://evil.example/cart", "products": [{"name": "x", "price": -1}],
        }))
        show("4. save_collection — not approved", await client.call_tool(
            "save_collection", {**COLLECTION, "cart_url": "https://vkusvill.ru/cart/share/mcp-demo-2", "operator_approved": False}))
        show("5. list_collections", await client.call_tool("list_collections", {"limit": 3}))

    async with Client(server("http://127.0.0.1:9")) as client:
        show("6. save_collection — service is down", await client.call_tool("save_collection", COLLECTION))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"))
