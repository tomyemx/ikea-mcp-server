from playwright.async_api import async_playwright
import asyncio

URL = "https://www.ikea.com/il/he/p/helmer-drawer-unit-on-castors-white-10251045/"

async def main():
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
        await page.goto(URL, timeout=60000, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000) # Wait for hydration
        
        await page.screenshot(path="helmer.png")
        content = await page.content()
        with open("helmer.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Saved helmer.png and helmer.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
