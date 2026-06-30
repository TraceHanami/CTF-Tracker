import requests
import time

url = "https://api.devfolio.co/api/hackathons?type=upcoming&page=1&per_page=10"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

print("Fetching Devfolio API with per_page=10...")
t0 = time.time()
resp = requests.get(url, headers=headers, timeout=15)
t1 = time.time()
print(f"Status: {resp.status_code}, Time: {t1 - t0:.2f}s")
if resp.status_code == 200:
    try:
        data = resp.json()
        print(f"Type of data: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            if "results" in data:
                print(f"Number of results: {len(data['results'])}")
                if data["results"]:
                    print(f"Sample item keys: {list(data['results'][0].keys())}")
            elif "hackathons" in data:
                print(f"Number of hackathons: {len(data['hackathons'])}")
        elif isinstance(data, list):
            print(f"Length of list: {len(data)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
