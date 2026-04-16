import requests
import xml.etree.ElementTree as ET

urls = []
r = requests.get('https://www.myscheme.gov.in/sitemap-0.xml')
root = ET.fromstring(r.content)
for c in root:
    urls.append(c[0].text)

print(f'Total URLs: {len(urls)}')
schemes = [u for u in urls if '/schemes/' in u]
print(f'Total Schemes: {len(schemes)}')
print('Sample:', schemes[:5])
