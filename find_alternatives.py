import asyncio
from playwright.async_api import async_playwright
import urllib.parse

# Items that failed verification
SEARCH_TERMS = [
    "MISTERHULT",
    "LISTERBY",
    "STOCKHOLM 2017",
    "VIGDIS",
    "SANDTRAV",
    "VOXLÖV",
    "NORRARYD"
]

search_url_template = "https://www.ikea.com/il/he/search/?q={}"

async def search_for_items():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Using headless for speed
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        found_urls = {}

        for term in SEARCH_TERMS:
            try:
                print(f"Searching for: {term}")
                encoded_term = urllib.parse.quote(term)
                await page.goto(search_url_template.format(encoded_term))
                await page.wait_for_load_state('networkidle')
                
                # Try to get the first product status
                # Selectors might be .plp-fragment-wrapper or similar
                # Let's try to grab the first anchor that looks like a product link
                
                # Check for "No results"
                no_results = await page.query_selector("text='לא נמצאו תוצאות'")
                if no_results:
                    print(f"  No results found for {term}")
                    continue

                # Try to find first product link
                # Common IKEA search result structure
                link_selector = ".plp-product-list__products > div > div > a" # Generic structure guess, might need refinement
                # Actually, let's grab any link containing '/p/' which usually denotes a product
                
                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('a'));
                    return anchors
                        .map(a => a.href)
                        .filter(href => href.includes('/p/') && !href.includes('search_result=true')); 
                }''')
                
                # Filter for links that actually look like product pages
                valid_links = [l for l in links if "/il/he/p/" in l]
                
                if valid_links:
                    print(f"  Found URL: {valid_links[0]}")
                    found_urls[term] = valid_links[0]
                else:
                    print(f"  No valid product links found for {term}")

            except Exception as e:
                print(f"  Error searching for {term}: {e}")
            
            await asyncio.sleep(1)

        await browser.close()
        return found_urls

if __name__ == "__main__":
    results = asyncio.run(search_for_items())
    print("\n--- Found URLs ---")
    for term, url in results.items():
        print(f'"{term}": "{url}",')
