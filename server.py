"""IKEA Israel MCP server.

Exposes the IKEA Israel sale catalogue as MCP tools. The server deliberately does no
LLM work of its own: it returns structured data and lets the calling client's model do
the styling, matching and recommending. See docs/SERVER-STATUS.md for why the earlier
MCP-Sampling design was dropped.
"""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ikea_scraper import get_product_details, scrape_ikea_sale

mcp = FastMCP("IkeaLivingRoomDesigner")

# Scraping the sale page takes ~20s, and a single conversation usually asks about it
# repeatedly. Cache per category for the life of the process.
_sale_cache: dict[str | None, list[dict[str, Any]]] = {}


@mcp.tool()
async def get_sale_items(category: str | None = None, limit: int = 50) -> str:
    """Fetch items currently on sale at IKEA Israel.

    Returns JSON: a list of items with name, description, price (ILS), image_url and
    product_url. Prices are as shown on the sale page. Product names are in Hebrew.

    Use this to answer questions about what is on offer, or to pick items that suit a
    room's style — analyse the returned list yourself rather than expecting the server
    to rank it.

    Args:
        category: Optional free-text filter matched against item name and description.
        limit: Maximum number of items to return (default 50).
    """
    if category not in _sale_cache:
        _sale_cache[category] = await scrape_ikea_sale(category)

    products = _sale_cache[category]
    if not products:
        return json.dumps(
            {
                "count": 0,
                "items": [],
                "note": "No sale items matched. The IKEA Israel sale page may be empty, "
                "or the category filter may be too narrow.",
            },
            ensure_ascii=False,
        )

    limited = products[: max(0, limit)]
    return json.dumps(
        {"count": len(limited), "total_available": len(products), "items": limited},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool()
async def check_product(url: str) -> str:
    """Check live price and availability for one IKEA Israel product URL.

    Returns JSON with status, price, whether the price includes VAT, and the product
    name. Sale listings go stale quickly, so verify anything before recommending it —
    a URL that redirects to a category page means the product is no longer available.

    Args:
        url: Full IKEA Israel product URL (https://www.ikea.com/il/he/p/...).
    """
    if not url.startswith("http"):
        return json.dumps({"error": f"Not a valid URL: {url}"}, ensure_ascii=False)

    details = await get_product_details(url)
    return json.dumps(details, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
