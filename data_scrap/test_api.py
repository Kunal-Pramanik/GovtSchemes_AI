import requests
import json
import re

url = "https://www.myscheme.gov.in/"
r = requests.get(url)
data = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)

if data:
    parsed = json.loads(data.group(1))
    print(list(parsed.keys()))
    if 'props' in parsed:
        print(list(parsed['props']['pageProps'].keys()))
else:
    print("Not found")
