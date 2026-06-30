import requests
import re

url = "https://www.hackerearth.com/challenges/"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

print(f"Requesting {url}...")
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Content Length: {len(resp.text)}")
    # Look for any JSON or API urls inside script tags
    urls = re.findall(r'https://[a-zA-Z0-9.-]+/api/[a-zA-Z0-9./?=&_-]+', resp.text)
    print(f"Found {len(urls)} API urls in html:")
    for u in set(urls[:20]):
        print(f"  {u}")
    
    # Check if there's a JSON string like window.__PRELOADED_STATE__ or similar
    matches = re.findall(r'(window\.[a-zA-Z0-9_]+\s*=\s*\{.*?\});', resp.text)
    print(f"Found {len(matches)} window states")
    
    # Save the response snippet to check structure
    with open("hec.txt", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print("Saved HTML to hec.txt")
else:
    print(resp.text[:1000])
