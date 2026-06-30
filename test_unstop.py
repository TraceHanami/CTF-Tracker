import requests

url = "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&filters[0][type]=location&filters[0][value]=online&per_page=30&page=1"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

print(f"Requesting {url}...")
resp = requests.get(url, headers=headers, timeout=15)
if resp.status_code == 200:
    data = resp.json()
    total = data.get('data', {}).get('total', 0)
    items = len(data.get('data', {}).get('data', []))
    print(f"-> Success: total={total}, items={items}")
    if items > 0:
        print(f"   Sample title: {data['data']['data'][0].get('title')}")
else:
    print(f"-> Status: {resp.status_code}")
