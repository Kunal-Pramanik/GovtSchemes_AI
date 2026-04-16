import requests
import json
import csv
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'x-api-key': API_KEY,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'origin': 'https://www.myscheme.gov.in',
    'referer': 'https://www.myscheme.gov.in/'
}

SEARCH_API_URL = "https://api.myscheme.gov.in/search/v6/schemes?lang=en&from={}&size={}&q=%5B%5D&keyword=&sort="
DETAILS_API_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug={}&lang=en"

def strip_html(obj):
    if not obj:
        return ""
    if isinstance(obj, str):
        return BeautifulSoup(obj, "html.parser").get_text(separator=' ', strip=True)
    elif isinstance(obj, dict):
        if 'text' in obj:
            return str(obj['text'])
        vals = []
        for k, v in obj.items():
            if k in ['children', 'content', 'items', 'details'] or isinstance(v, (dict, list)):
                extracted = strip_html(v)
                if extracted: vals.append(extracted)
        return " ".join(vals)
    elif isinstance(obj, list):
        return "\n".join([strip_html(item) for item in obj if item])
    return str(obj)

def smart_get(url):
    for attempt in range(6):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(2)
    return None

def get_all_slugs():
    slugs = []
    r = smart_get(SEARCH_API_URL.format(0, 1))
    if not r:
        print("Failed to contact API. Wait and try again later.")
        return []
    try:
        data = r.json()
        total_schemes = data['data']['summary']['total']
        print(f"Discovered a total of {total_schemes} schemes.")
    except Exception as e:
        print("Failed to get total schemes:", e)
        return []

    chunk_size = 100
    for offset in range(0, total_schemes, chunk_size):
        r = smart_get(SEARCH_API_URL.format(offset, chunk_size))
        if not r:
            continue
        try:
            items = r.json()['data']['hits']['items']
            for item in items:
                slugs.append({
                    'slug': item['fields']['slug'],
                    'basicInfo': item['fields']
                })
            print(f"Fetched {len(slugs)}/{total_schemes} slugs.")
            time.sleep(1) # Prevent 429 on listing
        except Exception as e:
            print(f"Failed to fetch chunk {offset}:", e)
    
    return slugs

def fetch_scheme_details(scheme_data):
    slug = scheme_data['slug']
    basic = scheme_data['basicInfo']
    
    for attempt in range(6):
        try:
            r = requests.get(DETAILS_API_URL.format(slug), headers=HEADERS, timeout=15)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code != 200:
                print(f"Failed {slug}: HTTP {r.status_code}")
                return None
            
            data = r.json()['data']['en']
            
            details_str = data.get('schemeContent', {}).get('detailedDescription_md', '')
            if not details_str: 
                details_str = data.get('schemeContent', {}).get('detailedDescription', '')
            if not details_str:
                details_str = data.get('schemeContent', {}).get('briefDescription', '')
                
            benefits_list = data.get('schemeContent', {}).get('benefits', [])
            
            eligibility = data.get('eligibilityCriteria', {}).get('eligibilityDescription_md', '')
            if not eligibility:
                eligibility = data.get('eligibilityCriteria', {}).get('eligibilityDescription', '')
            if not eligibility:
                criteria_rules = data.get('eligibilityCriteria', {}).get('rules', [])
                eligibility = "\n".join([str(x) for x in criteria_rules])

            app_process = data.get('applicationProcess', [])
            app_str = ""
            for mode in app_process:
                mode_name = mode.get('mode', 'Process')
                steps = mode.get('process', [])
                app_str += f"{mode_name}:\n"
                for s in steps:
                    app_str += f"- {s.get('text', '')}\n"
                    
            return {
                'Scheme Name': basic.get('schemeName', ''),
                'Short Title': basic.get('schemeShortTitle', ''),
                'Category': basic.get('schemeCategory', ''),
                'Level': basic.get('level', ''),
                'State': basic.get('beneficiaryState', ''),
                'Nodal Ministry': basic.get('nodalMinistryName', ''),
                'Priority': basic.get('priority', ''),
                'Details': strip_html(details_str),
                'Benefits': strip_html(benefits_list),
                'Eligibility Criteria': strip_html(eligibility),
                'Application Process': strip_html(app_str)
            }
        except Exception as e:
            if attempt == 4:
                print(f"Error {slug}: {e}")
            time.sleep(1)
            
    return None

def main():
    slugs = get_all_slugs()
    if not slugs:
        return
        
    all_schemes = []
    print(f"Fetching details for {len(slugs)} schemes...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_scheme_details, sd): sd for sd in slugs}
        count = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_schemes.append(res)
            count += 1
            if count % 100 == 0:
                print(f"Progress: {count}/{len(slugs)}")
                
                # Intermediate save
                with open('schemes_data.json', 'w', encoding='utf-8') as f:
                    json.dump(all_schemes, f, ensure_ascii=False, indent=2)
                    
    print("Done. Saving final files...")
    with open('schemes_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_schemes, f, ensure_ascii=False, indent=2)
        
    if all_schemes:
        keys = all_schemes[0].keys()
        with open('schemes_data.csv', 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_schemes)
            
if __name__ == "__main__":
    main()
