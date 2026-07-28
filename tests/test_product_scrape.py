from playwright.async_api import async_playwright
import asyncio

# Known working URL from the sale list
URL_KNOWN = "https://www.ikea.com/il/he/p/helmer-drawer-unit-on-castors-white-10251045/"
# The problematic one
URL_PROBLEM = "https://www.ikea.com/il/he/p/ekenaeset-armchair-kilanda-light-beige-00533493/"

async def fetch_product_page(url, name):
    print(f"--- Testing {name} ---")
    async with async_playwright() as p:
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
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)
        
        page = await context.new_page()
        try:
            print(f"Navigating to {url}")
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Wait for meaningful content
            try:
                await page.wait_for_selector('.pip-product-summary, .pip-layout__main', timeout=10000)
                print("Product page loaded (selector found).")
            except:
                print("Product selector not found (might have redirected).")
                
            print(f"Current URL: {page.url}")
            
            # Helper to find price
            price_el = await page.query_selector('.pip-temp-price__integer, .pip-price__integer')
            if price_el:
                print(f"Detected Price: {await price_el.inner_text()}")
            else:
                print("Price element not found.")
                
            # Helper to find availability
            # Looking for the generic "Available for delivery" or logic
            avail_panel = await page.query_selector('.pip-availability-modal-open-button')
            if avail_panel:
                print(f"Availability Button Text: {await avail_panel.inner_text()}")
            
            # Check for "Not available" text
            body_text = await page.inner_text('body')
            if "לא זמין" in body_text or "חסר במלאי" in body_text:
                print("Found 'Not Available' text/keywords in body.")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

async def main():
    await fetch_product_page(URL_KNOWN, "HELMER (Known)")
    await fetch_product_page(URL_PROBLEM, "EKENASET (Problem)")

if __name__ == "__main__":
    asyncio.run(main())
