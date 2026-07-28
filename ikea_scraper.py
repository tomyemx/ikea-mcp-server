from playwright.async_api import async_playwright
import json
import asyncio
import os
import sys

HEADLESS = True

# This module runs inside an MCP stdio server, where stdout carries the JSON-RPC
# stream. Anything written there corrupts the protocol, so all progress output goes
# to stderr.
def _log(message):
    print(message, file=sys.stderr, flush=True)


# Debug dumps go next to this file, not to whatever CWD the MCP client happened to use.
_HERE = os.path.dirname(os.path.abspath(__file__))

SALE_URL = "https://www.ikea.com/il/he/offers/limited-time-offers/"

# The sale hub carries ~2,100 items. Category-scoped offer pages are far smaller and
# usually what you actually want.
CATEGORY_URLS = {
    "sofas-armchairs": "https://www.ikea.com/il/he/offers/deals-on-sofas-armchairs-living-room-seating-offers-700640/",
    "tables-chairs": "https://www.ikea.com/il/he/offers/deals-on-tables-chairs-offers-fu002/",
    "desks-office-chairs": "https://www.ikea.com/il/he/offers/deals-on-office-desks-chairs-furniture-offers-fu004/",
}

# Product cards expose a stable test id; the class names around them churn.
CARD_SELECTOR = '[data-testid="plp-product-card"], .plp-fragment-wrapper, .pub__product-card, .product-compact'

# How many times a "show more" batch may fail to appear before we call it the end.
MAX_STALLS = 3


async def scrape_ikea_sale(category_filter: str = None, url: str = None, max_items: int = 200):
    """
    Scrapes an IKEA Israel offers page for products.

    Args:
        category_filter: optional free-text filter on name/description.
        url: offers page to scrape; defaults to the full sale hub. Accepts a key from
             CATEGORY_URLS as a shorthand.
        max_items: stop paginating once this many cards are loaded. The hub has ~2,100
                   items and each "show more" click costs a round trip, so this matters.

    Returns a list of dicts: name, description, price, price_before, discount,
    image_url, product_url. `price` is what you pay; `price_before` is the struck-out
    original, present only on discounted items.
    """
    url = CATEGORY_URLS.get(url, url) or SALE_URL
    async with async_playwright() as p:
        # Launch with arguments to try and avoid detection
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Add init script to remove webdriver property
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)
        
        page = await context.new_page()
        
        _log(f"Navigating to {url}...")
        try:
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')
        except Exception as e:
            _log(f"Navigation error: {e}")

        try:
            await page.wait_for_selector(CARD_SELECTOR, timeout=15000)
        except Exception:
            _log("Timeout waiting for product cards.")

        # IKEA paginates: 24 cards per page behind a "הצג עוד" control. Without clicking
        # it we only ever saw the first page — which silently capped every result at 24.
        total_text = await page.evaluate(
            r"""() => { const m = document.body.innerText.match(/([\d,]+)\s*פריטים/); return m ? m[1] : null; }"""
        )
        if total_text:
            _log(f"Page reports {total_text} items available.")

        count = await page.evaluate(f"document.querySelectorAll('{CARD_SELECTOR}').length")
        stalls = 0
        while count < max_items:
            # Match on the control's text, not its CSS classes, which churn between
            # releases. Re-locate every pass — the control is re-rendered on each load.
            more = page.locator("a,button").filter(has_text="הצג עוד").first
            try:
                if not await more.count() or not await more.is_visible():
                    break  # button really is gone: end of list
                await more.scroll_into_view_if_needed(timeout=5000)
                await more.click(timeout=5000)
            except Exception as e:
                _log(f"Pagination stopped: {e}")
                break

            try:
                await page.wait_for_function(
                    f"document.querySelectorAll('{CARD_SELECTOR}').length > {count}", timeout=15000
                )
            except Exception:
                # A slow batch looks exactly like the end of the list. Only the button
                # disappearing proves we are done, so retry before believing it —
                # without this the scrape silently truncated at 48 of 126 items.
                stalls += 1
                if stalls >= MAX_STALLS:
                    _log(f"No new cards after {stalls} attempts; assuming end of list.")
                    break
                _log(f"Batch stalled ({stalls}/{MAX_STALLS}); retrying...")
                continue

            new_count = await page.evaluate(f"document.querySelectorAll('{CARD_SELECTOR}').length")
            if new_count <= count:  # belt-and-braces against an infinite loop
                break
            count = new_count
            stalls = 0
            _log(f"Loaded {count} cards...")

        _log(f"Collecting {count} product cards.")

        products = await page.evaluate('''(cardSelector) => {
            const text = el => el ? el.innerText.trim() : null;

            return Array.from(document.querySelectorAll(cardSelector)).map(el => {
                const nameEl = el.querySelector('.plp-price-module__name-decorator, .notranslate, .pip-header-section__title--small, .pub__title, h3');
                const descEl = el.querySelector('.plp-price-module__description, .pip-header-section__description-text, .pub__description');
                const imgEl  = el.querySelector('img');
                const linkEl = el.querySelector('a[href*="/p/"]') || el.querySelector('a');

                // A discounted card renders TWO .plp-price__integer nodes: the struck-out
                // original first, then the price you actually pay. Selecting the first one
                // is the bug that made every quoted price too high.
                const current = el.querySelector('.plp-price-module__primary-currency-price-energy-class .plp-price__integer');
                const before  = el.querySelector('.plp-price-module__comparison-price .plp-price__integer');
                const all = Array.from(el.querySelectorAll('.plp-price__integer, .pip-price__integer, .pip-temp-price__integer'));

                // Fall back on DOM order: the payable price is always last.
                const price = text(current) || (all.length ? text(all[all.length - 1]) : null);
                const priceBefore = text(before) || (all.length > 1 ? text(all[0]) : null);

                if (!nameEl || !price) return null;

                return {
                    name: nameEl.innerText.trim(),
                    description: descEl ? descEl.innerText.trim() : "",
                    price: price,
                    price_before: priceBefore === price ? null : priceBefore,
                    discount: text(el.querySelector('.plp-price-module__offer-message')),
                    image_url: imgEl ? imgEl.src : "",
                    product_url: linkEl ? linkEl.href : ""
                };
            }).filter(p => p !== null);
        }''', CARD_SELECTOR)

        # The same product can render more than one card (variant boxes); dedupe on URL.
        seen = set()
        deduped = []
        for p in products:
            key = p.get("product_url") or (p["name"], p["price"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)
        if len(deduped) != len(products):
            _log(f"Deduped {len(products)} cards -> {len(deduped)} products.")
        products = deduped
        
        if not products:
            _log("No products found on sale page. Dumping content and screenshot...")
            content = await page.content()
            await page.screenshot(path=os.path.join(_HERE, "debug_screenshot.png"))
            with open(os.path.join(_HERE, "sale_page_dump.html"), "w", encoding="utf-8") as f:
                f.write(content)

        await browser.close()

        # Simple local filtering if category is provided
        if category_filter:
            _log(f"Filtering for '{category_filter}' in {len(products)} products...")
            filtered = [p for p in products if category_filter.lower() in p['name'].lower() or category_filter.lower() in p['description'].lower()]
            return filtered
            
        return products

async def get_product_details(url):
    """
    Fetches real-time price and availability status for a specific product URL.
    Returns a dict with 'price', 'currency', 'status', 'name'.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
        )
        context = await browser.new_context()
        # Stealth mode
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        result = {
            "url": url,
            "status": "Unknown",
            "price": None,
            "vat_included": False
        }
        
        try:
            await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # 1. Check for Redirect (Category Page = Item Unavailable)
            if "cat/products" in page.url or "cat/items" in page.url:
                result["status"] = "Unavailable (Redirected)"
                await browser.close()
                return result
                
            # 2. Extract Data from utag_data (Global Variable)
            try:
                # utag_data usually contains: "price":["195"], "product_prices":["165.25"] (ex VAT)
                data = await page.evaluate("window.utag_data")
                if data:
                    result["status"] = "Available"
                    
                    # Try to find the VAT-inclusive price first ("price")
                    if "price" in data and len(data["price"]) > 0:
                        result["price"] = float(data["price"][0])
                        result["vat_included"] = True
                    # Fallback to ex-VAT price ("product_prices")
                    elif "product_prices" in data and len(data["product_prices"]) > 0:
                        result["price"] = float(data["product_prices"][0])
                        result["vat_included"] = False # Needs * 1.17
                        
                    if "product_names" in data:
                        result["name"] = data["product_names"][0]
            except Exception as e:
                _log(f"Error extracting utag_data: {e}")
                
        except Exception as e:
            result["status"] = f"Error: {str(e)[:50]}"
            
        await browser.close()
        return result

if __name__ == "__main__":
    # Usage: python ikea_scraper.py [category-key-or-url] [max_items]
    target = sys.argv[1] if len(sys.argv) > 1 else None
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    results = asyncio.run(scrape_ikea_sale(None, url=target, max_items=cap))
    discounted = [p for p in results if p.get("price_before")]
    print(f"Found {len(results)} products ({len(discounted)} discounted).")
    print(json.dumps(results[:3], indent=2, ensure_ascii=False))
