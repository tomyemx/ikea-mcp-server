"""End-to-end check: launch server.py as a real MCP stdio server and drive it over the
protocol, the same way Claude Code or Antigravity would.

Run directly:  .venv\\Scripts\\python.exe tests\\test_server_flow.py
Hits the live IKEA Israel site, so it needs network and takes ~30s.
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(REPO, "server.py")],
        cwd=REPO,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"tools advertised: {names}")
            assert "get_sale_items" in names, "get_sale_items missing"
            assert "check_product" in names, "check_product missing"

            print("\ncalling get_sale_items(limit=3)...")
            result = await session.call_tool("get_sale_items", {"limit": 3})
            payload = json.loads(result.content[0].text)
            print(f"  count={payload['count']} total_available={payload.get('total_available')}")
            assert payload["count"] > 0, "no sale items returned"

            first = payload["items"][0]
            for field in ("name", "price", "image_url", "product_url"):
                assert first.get(field), f"item missing {field}"
            print(f"  first item: {first['name'].splitlines()[0]} @ {first['price']} ILS")

            print("\ncalling check_product() on that item...")
            result = await session.call_tool("check_product", {"url": first["product_url"]})
            details = json.loads(result.content[0].text)
            print(f"  status={details['status']} price={details.get('price')}")
            assert details["status"] != "Unknown", "product check returned Unknown"

    print("\nAll checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
