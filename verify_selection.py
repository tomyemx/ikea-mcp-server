import asyncio
import json
from ikea_scraper import get_product_details

# Validated URLs for the final list
ITEMS_TO_VERIFY = [
    # Lighting
    "https://www.ikea.com/il/he/p/sinnerlig-pendant-lamp-bamboo-70311697/", # SINNERLIG (Lamp)
    "https://www.ikea.com/il/he/p/misterhult-pendant-lamp-bamboo-handmade-90441018/", # MISTERHULT (Pendant)

    # Furniture
    "https://www.ikea.com/il/he/p/listerby-coffee-table-oak-veneer-30513904/", # LISTERBY (Coffee Table)
    "https://www.ikea.com/il/he/p/vedbo-armchair-gunnared-light-brown-pink-40423578/", # VEDBO (Armchair - previously verified)
    
    # Textiles/Decor
    "https://www.ikea.com/il/he/p/lohals-rug-flatwoven-natural-00277395/", # LOHALS (Rug - previously verified)
    "https://www.ikea.com/il/he/p/sandtrav-cushion-grey-green-white-80563449/", # SANDTRAV (Cushion)
    
    # Storage (Previously verified, keeping for context)
    "https://www.ikea.com/il/he/p/trofast-wall-storage-light-white-stained-pine-white-s69102306/", # TROFAST
]

async def verify_items():
    print(f"Verifying {len(ITEMS_TO_VERIFY)} confirmed items...")
    results = []
    
    for url in ITEMS_TO_VERIFY:
        print(f"Checking: {url}")
        details = await get_product_details(url)
        # Add a manual name override if needed or just trust the scraper
        results.append(details)
        await asyncio.sleep(2)

    return results

if __name__ == "__main__":
    results = asyncio.run(verify_items())
    
    print("\n--- Final Verified List ---")
    total_cost = 0
    
    for item in results:
        status_icon = "✅" if item['status'] == 'Available' else "❌"
        price = item.get('price')
        price_display = f"{price} ILS" if price else "N/A"
        
        print(f"{status_icon} {item.get('name', 'Unknown')}: {price_display} ({item.get('url')})")
        
        if item['status'] == 'Available' and price:
            total_cost += price

    print(f"\nTotal Estimated Cost: {total_cost:.2f} ILS")
