import asyncio
import json
from ikea_scraper import get_product_details

# Trying specific URLs for storage
ITEMS_TO_VERIFY = [
    # TROFAST (Pine/White)
    "https://www.ikea.com/il/he/p/trofast-storage-combination-with-boxes-light-white-stained-pine-white-s29103007/",
    # FLISAT Book Display
    "https://www.ikea.com/il/he/p/flisat-book-display-00290820/",
    # KALLAX (White wood effect)
    "https://www.ikea.com/il/he/p/kallax-shelving-unit-white-stained-oak-effect-00324518/",
    # BRANAS Basket
    "https://www.ikea.com/il/he/p/branaes-basket-rattan-00138432/"
]

async def verify_items():
    print(f"Verifying {len(ITEMS_TO_VERIFY)} items...")
    results = []
    
    for url in ITEMS_TO_VERIFY:
        print(f"Checking: {url}")
        details = await get_product_details(url)
        print(f"Result: {details}")
        results.append(details)
        await asyncio.sleep(2) # be nice

    return results

if __name__ == "__main__":
    results = asyncio.run(verify_items())
    
    print("\n--- Storage Items Verification ---")
    for item in results:
        status_icon = "✅" if item['status'] == 'Available' else "❌"
        print(f"{status_icon} {item.get('name', 'Unknown')}: {item.get('price', 'N/A')} ILS ({item['url']})")
