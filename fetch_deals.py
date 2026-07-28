import asyncio
import json
from ikea_scraper import scrape_ikea_sale

async def main():
    print("Scraping all deals...")
    products = await scrape_ikea_sale(None)
    print(f"Found {len(products)} products.")
    
    with open("all_deals.json", "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print("Saved to all_deals.json")

if __name__ == "__main__":
    asyncio.run(main())
