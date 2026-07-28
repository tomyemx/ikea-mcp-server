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

async def scrape_ikea_sale(category_filter: str = None):
    """
    Scrapes the IKEA Israel sale page for products.
    Returns a list of dictionaries with product details.
    """
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
        
        _log(f"Navigating to {SALE_URL}...")
        try:
            await page.goto(SALE_URL, timeout=60000, wait_until='domcontentloaded')
        except Exception as e:
            _log(f"Navigation error: {e}")

        # Scroll to bottom to trigger lazy loading
        _log("Scrolling to load products...")
        for i in range(10):
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(1000)
            
        # Explicitly wait for product cards
        try:
            await page.wait_for_selector('.plp-fragment-wrapper, .pub__product-card, .product-compact', timeout=10000)
            _log("Product cards detected!")
        except:
            _log("Timeout waiting for product cards.")

        # Try to find product elements using standard IKEA global site selectors
        products = await page.evaluate('''() => {
            const items = [];
            
            // Standard IKEA product card selectors (global site)
            // .pub__product-card, .plp-fragment-wrapper, .pip-product-compact
            
            const cards = document.querySelectorAll('.plp-fragment-wrapper, .pub__product-card, .product-compact, [data-testid="plp-product-card"]');
            
            if (cards.length > 0) {
                 return Array.from(cards).map(el => {
                    // Extract info
                    const nameEl = el.querySelector('.notranslate, .pip-header-section__title--small, .pub__title, h3');
                    const descEl = el.querySelector('.pip-header-section__description-text, .pub__description');
                    const priceEl = el.querySelector('.pip-price__integer, .pub__price__value, .pip-temp-price__integer, .plp-price__integer'); 
                    const imgEl = el.querySelector('img');
                    const linkEl = el.querySelector('a');
                    
                    if (!nameEl) return null;
                    
                    return {
                        name: nameEl.innerText.trim(),
                        description: descEl ? descEl.innerText.trim() : "",
                        price: priceEl ? priceEl.innerText.trim() : "N/A",
                        image_url: imgEl ? imgEl.src : "",
                        product_url: linkEl ? linkEl.href : ""
                    };
                 }).filter(p => p !== null && p.price !== "N/A");
            }
            
            return [];
        }''')
        
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
    # Test run
    # data = asyncio.run(scrape_ikea_deals())
    # print(f"Found {len(data)} deals")
    
    # Test details
    res = asyncio.run(get_product_details("https://www.ikea.com/il/he/p/helmer-drawer-unit-on-castors-white-10251045/"))
    print(res)
    results = asyncio.run(scrape_ikea_sale(None))
    print(f"Found {len(results)} products.")
    print(json.dumps(results[:3], indent=2, ensure_ascii=False))
