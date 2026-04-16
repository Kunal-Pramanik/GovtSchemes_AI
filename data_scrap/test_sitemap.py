import requests
import xml.etree.ElementTree as ET

urls = []
try:
    r = requests.get('https://www.myscheme.gov.in/sitemap.xml')
    if r.status_code == 200:
        print("Found sitemap.xml")
        root = ET.fromstring(r.content)
        for child in root:
            for subchild in child:
                if 'loc' in subchild.tag:
                    urls.append(subchild.text)
        print("Total URLs:", len(urls))
        print("Sample:", urls[:10])
    else:
        print("sitemap.xml not found")
except Exception as e:
    print(e)
