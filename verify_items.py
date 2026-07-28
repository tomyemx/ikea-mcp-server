from playwright.async_api import async_playwright
import asyncio
import json

URLS = {
    "EKENAS": "https://www.ikea.com/il/he/p/ekenaeset-armchair-kilanda-light-beige-00533493/",
    "VEDBO": "https://www.ikea.com/il/he/p/vedbo-armchair-gunnared-light-brown-pink-40423578/",
    "LOHALS": "https://www.ikea.com/il/he/p/lohals-rug-flatwoven-natural-00277395/",
    "TROFAST": "https://www.ikea.com/il/he/p/trofast-wall-storage-light-white-stained-pine-white-s19575489/",
    "SMASTAD": "https://www.ikea.com/il/he/p/smastad-wardrobe-white-white-s09549071/",
    "KOPPANG": "https://www.ikea.com/il/he/p/koppang-chest-of-6-drawers-white-10311308/"
}

async def check_item(context, name, url):
    page = await context.new_page()
    result = {"name": name, "url": url, "status": "unknown", "price": "N/A"}
    
    try:
        # print(f"Checking {name}...")
        await page.goto(url, timeout=30000, wait_until='domcontentloaded')
        
        # Check URL for redirect
        if "cat/products" in page.url or "cat/items" in page.url:
            result["status"] = "Redirected (Likely Out of Stock)"
        else:
            result["status"] = "Page Loaded"
            # Try to get utag_data
            try:
                data = await page.evaluate("window.utag_data")
                if data and "product_prices" in data:
                    result["price"] = data["product_prices"][0]
                elif data and "price" in data:
                    result["price"] = data["price"][0]
            except:
                pass
                
    except Exception as e:
        result["status"] = f"Error: {str(e)[:50]}"
        
    await page.close()
    return result

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
        )
        context = await browser.new_context()
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        tasks = []
        for name, url in URLS.items():
            tasks.append(check_item(context, name, url))
            
        results = await asyncio.gather(*tasks)
        print(json.dumps(results, indent=2))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
