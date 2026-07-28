import asyncio
from ikea_scraper import get_product_details

# Scandi/Boho Bedroom Selection
ITEMS_TO_VERIFY = [
    # Bedding
    "https://www.ikea.com/il/he/p/nattjasmin-duvet-cover-and-2-pillowcases-white-20337162/", # NATTJASMIN (White)
    "https://www.ikea.com/il/he/p/aengslilja-duvet-cover-and-2-pillowcases-beige-70318661/", # ANGSLILJA (Beige)
    
    # Rugs (Smaller for bedside)
    "https://www.ikea.com/il/he/p/lohals-rug-flatwoven-natural-20307481/", # LOHALS (80x150)
    "https://www.ikea.com/il/he/p/stoense-rug-low-pile-off-white-00426803/", # STOENSE
    
    # Lighting
    "https://www.ikea.com/il/he/p/knixhult-table-lamp-bamboo-60358529/", # KNIXHULT (Table)
    "https://www.ikea.com/il/he/p/knixhult-pendant-lamp-bamboo-40404886/", # KNIXHULT (Pendant)
    
    # Curtains/Decor
    "https://www.ikea.com/il/he/p/hilja-curtains-1-pair-white-50430818/", # HILJA
    "https://www.ikea.com/il/he/p/lindbyn-mirror-black-50458614/" # LINDBYN (Mirror)
]

async def verify_bedroom_items():
    print(f"Verifying {len(ITEMS_TO_VERIFY)} bedroom items...")
    results = []
    
    for url in ITEMS_TO_VERIFY:
        print(f"Checking: {url}")
        details = await get_product_details(url)
        results.append(details)
        await asyncio.sleep(1)

    return results

if __name__ == "__main__":
    results = asyncio.run(verify_bedroom_items())
    
    print("\n--- Verified Bedroom Items ---")
    for item in results:
        status_icon = "✅" if item['status'] == 'Available' else "❌"
        print(f"{status_icon} {item.get('name', 'Unknown')}: {item.get('price', 'N/A')} ILS ({item['url']})")
