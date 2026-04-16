import requests
import json
import re

url = "https://www.myscheme.gov.in/search"
r = requests.get(url)
data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)

if data:
    parsed = json.loads(data.group(1))
    print("Keys in pageProps:", list(parsed['props']['pageProps'].keys()))
    with open("next_data.json", "w") as f:
        json.dump(parsed, f, indent=2)
else:
    print("Not found")
