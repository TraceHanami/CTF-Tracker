import re

with open("next_f_extracted.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Find anything that looks like an API URL or json
urls = re.findall(r'https://[a-zA-Z0-9.-]+/api/[a-zA-Z0-9./?=&_-]+', content)
print(f"Found {len(urls)} API urls:")
for u in set(urls):
    print(f"  {u}")

# Find any strings containing "challenge" or "hackathon"
matches = re.findall(r'"[^"]*hackathon[^"]*"|"[^"]*challenge[^"]*"', content, re.IGNORECASE)
print(f"\nFound {len(matches)} matches for hackathon/challenge in strings:")
for m in set(matches[:20]):
    print(f"  {m}")

# Let's print the length of content
print(f"\nTotal length of Next.js streams: {len(content)}")
