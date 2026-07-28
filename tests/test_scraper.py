import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get('https://www.ikea.co.il/', headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        with open('ikea_home.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Saved ikea_home.html")
    else:
        print("Failed to fetch page")
except Exception as e:
    print(f"Error: {e}")
