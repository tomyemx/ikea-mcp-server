import asyncio
from playwright.async_api import async_playwright
import urllib.parse
from ikea_scraper import get_product_details

# Potential storage items for Scandi/Boho
SEARCH_TERMS = [
    "TROFAST", # Frame, pine
    "FLISAT", # Book display / Toy storage
    "KALLAX", # Shelving unit
    "BRANÄS", # Basket
    "LUSTIGKURRE" # Basket
]

search_url_template = "https://www.ikea.com/il/he/search/?q={}"

async def find_and_verify_storage():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        found_products = []

        print("--- Searching for Storage Solutions ---")
        for term in SEARCH_TERMS:
            try:
                print(f"Searching for: {term}")
                encoded_term = urllib.parse.quote(term)
                await page.goto(search_url_template.format(encoded_term))
                await page.wait_for_load_state('networkidle')
                
                # Extract first few valid product links
                links = await page.evaluate('''() => {
                    const anchors = Array.from(document.querySelectorAll('.plp-product-list__products > div > div > a'));
                    return anchors
                        .map(a => a.href)
                        .filter(href => href.includes('/p/') && !href.includes('search_result=true'))
                        .slice(0, 3); // Take top 3 to check specifics
                }''')
                
                for url in links:
                    print(f"  Checking URL: {url}")
                    details = await get_product_details(url)
                    print(f"    Details: {details}")
                    
                    if details['status'] == 'Available' or True: # Force accept for now to see what we get
                        found_products.append(details)
                        print(f"  ✅ Added candidate: {details.get('name', 'Unknown')}")
                        break 
            except Exception as e:
                print(f"  Error searching for {term}: {e}")
            
            await asyncio.sleep(1)

        await browser.close()
        return found_products

if __name__ == "__main__":
    results = asyncio.run(find_and_verify_storage())
    
    print("\n--- Selected Storage Items ---")
    for item in results:
        print(f"Name: {item.get('name')}")
        print(f"Price: {item.get('price')} ILS")
        print(f"URL: {item.get('url')}")
        print("-" * 20)
