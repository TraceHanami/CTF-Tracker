import re
from bs4 import BeautifulSoup
import json

with open("hec.txt", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

print("Checking title:", soup.title.string if soup.title else "No title")

# Find all scripts
scripts = soup.find_all("script")
print(f"Found {len(scripts)} scripts")

for idx, s in enumerate(scripts):
    text = s.string or ""
    if not text:
        continue
    print(f"Script {idx}: length={len(text)}, content preview={text[:200]}")
    if "challenges" in text.lower() or "hackathon" in text.lower():
        print(f"   => Matches keywords!")

# Let's search for "self.__next_f.push"
next_f = [s.string for s in scripts if s.string and "self.__next_f.push" in s.string]
print(f"Found {len(next_f)} next_f streams")
if next_f:
    print("Preview of first next_f stream:")
    print(next_f[0][:500])
    
    # Let's dump all text parts from next_f streams to a file
    with open("next_f_extracted.txt", "w", encoding="utf-8") as out:
        for nf in next_f:
            out.write(nf + "\n")
    print("Saved next_f streams to next_f_extracted.txt")
