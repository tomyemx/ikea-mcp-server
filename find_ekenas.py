from playwright.async_api import async_playwright
import asyncio

async def search_product():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Search URL
        search_url = "https://www.ikea.com/il/he/search/?q=EKEN%C3%84SET"
        print(f"Navigating to {search_url}")
        await page.goto(search_url)
        
        try:
            await page.wait_for_selector('.search-result-list', timeout=10000)
            # Get first result
            first_result = await page.query_selector('.plp-fragment-wrapper a')
            if first_result:
                href = await first_result.get_attribute('href')
                print(f"Found URL: {href}")
            else:
                print("No results found in list.")
        except:
            print("Search results didn't load.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(search_product())
