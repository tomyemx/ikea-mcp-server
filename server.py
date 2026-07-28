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

# Scraping takes ~20s and grows with pagination; a conversation usually asks repeatedly.
# The key must include the source page, or one category's results mask another's.
_sale_cache: dict[tuple[str | None, str | None, int], list[dict[str, Any]]] = {}


@mcp.tool()
async def get_sale_items(
    category: str | None = None,
    limit: int = 50,
    category_url: str | None = None,
    max_items: int = 200,
) -> str:
    """Fetch items currently on sale at IKEA Israel.

    Returns JSON per item: name, description, `price` (what you pay, ILS),
    `price_before` (struck-out original, null if not discounted), `discount`
    (e.g. "24% הנחה"), image_url and product_url. Product names are in Hebrew.

    The full sale hub carries ~2,100 items. Prefer a category page when you know what
    you are looking for — pass `category_url` as one of:
        sofas-armchairs, tables-chairs, desks-office-chairs
    or a full IKEA offers URL.

    Args:
        category: Optional free-text filter matched against item name and description.
        limit: Maximum number of items to return (default 50).
        category_url: Category shorthand or full offers URL. Defaults to the sale hub.
        max_items: How many cards to paginate through before stopping (default 200).
    """
    key = (category, category_url, max_items)
    if key not in _sale_cache:
        _sale_cache[key] = await scrape_ikea_sale(
            category, url=category_url, max_items=max_items
        )

    products = _sale_cache[key]
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
