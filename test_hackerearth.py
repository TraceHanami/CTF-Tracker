import requests

url = "https://www.hackerearth.com/api/v3/challenges/?type=hackathon&status=upcoming"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

print(f"Requesting {url}...")
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    try:
        data = resp.json()
        print(f"Keys: {list(data.keys())}")
        print(f"Total results: {len(data.get('results', []))}")
        if data.get('results'):
            print(f"Sample result: {data['results'][0]}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Snippet of response: {resp.text[:500]}")
else:
    print(f"Response: {resp.text[:500]}")
