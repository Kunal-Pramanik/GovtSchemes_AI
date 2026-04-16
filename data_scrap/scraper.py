import requests
import json
import csv
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'x-api-key': API_KEY,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

SEARCH_API_URL = "https://api.myscheme.gov.in/search/v6/schemes?lang=en&q=%5B%5D&keyword=&sort=&from={}&size={}"
DETAILS_API_URL = "https://api.myscheme.gov.in/schemes/v6/public/schemes?slug={}&lang=en"

def strip_html(html_data):
    if not html_data:
        return ""
    if isinstance(html_data, list):
        # some properties like benefits can be a list of dicts/strings
        cleaned = []
        for item in html_data:
            if isinstance(item, str):
                cleaned.append(BeautifulSoup(item, "html.parser").get_text(separator=' ', strip=True))
            elif isinstance(item, dict):
                content = item.get('content', '') or item.get('details', '') or str(item)
                cleaned.append(BeautifulSoup(content, "html.parser").get_text(separator=' ', strip=True))
        return "\n".join(cleaned)
    elif isinstance(html_data, str):
        return BeautifulSoup(html_data, "html.parser").get_text(separator=' ', strip=True)
    return str(html_data)

def get_all_slugs():
    slugs = []
    # Fetch first page to get total size
    try:
        r = requests.get(SEARCH_API_URL.format(0, 1), headers=HEADERS)
        data = r.json()
        total_schemes = data['data']['summary']['total']
        print(f"Discovered a total of {total_schemes} schemes.")
    except Exception as e:
        print("Failed to get total schemes:", e)
        return []

    # Get all schemes in chunks of 500
    chunk_size = 500
    for offset in range(0, total_schemes, chunk_size):
        try:
            r = requests.get(SEARCH_API_URL.format(offset, chunk_size), headers=HEADERS)
            items = r.json()['data']['hits']['items']
            for item in items:
                slugs.append({
                    'slug': item['fields']['slug'],
                    'basicInfo': item['fields']
                })
            print(f"Fetched {len(slugs)}/{total_schemes} basic scheme profiles.")
        except Exception as e:
            print(f"Failed to fetch chunk at offset {offset}:", e)
    
    return slugs

def fetch_scheme_details(scheme_data):
    slug = scheme_data['slug']
    basic = scheme_data['basicInfo']
    try:
        r = requests.get(DETAILS_API_URL.format(slug), headers=HEADERS, timeout=10)
        data = r.json()['data']['en']
        
        # Details
        details = data.get('schemeContent', {}).get('detailedDescription', '')
        if not details: details = data.get('schemeContent', {}).get('briefDescription', '')
            
        # Benefits
        benefits = data.get('schemeContent', {}).get('benefits', [])
        
        # Eligibility
        eligibility = data.get('eligibilityCriteria', {}).get('description', '')
        if not eligibility:
            # Maybe some nested lists
            criteria_rules = data.get('eligibilityCriteria', {}).get('rules', [])
            eligibility = "\n".join([str(x) for x in criteria_rules])

        # Application Process
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
            'Tags': basic.get('tags', ''),
            'Priority': basic.get('priority', ''),
            'Details': strip_html(details),
            'Benefits': strip_html(benefits),
            'Eligibility Criteria': strip_html(eligibility),
            'Application Process': strip_html(app_str)
        }
    except Exception as e:
        print(f"Error fetching details for {slug}: {e}")
        return None

def main():
    slugs = get_all_slugs()
    
    all_schemes = []
    
    # We will use multithreading to fetch the details fast
    print(f"Fetching details for {len(slugs)} schemes using multithreading...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_scheme_details, sd): sd for sd in slugs}
        
        count = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_schemes.append(res)
            count += 1
            if count % 100 == 0:
                print(f"Progress: {count}/{len(slugs)}")
                
    print("Done fetching details. Saving to files...")
    
    # Save to JSON
    with open('schemes_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_schemes, f, ensure_ascii=False, indent=2)
        
    # Save to CSV
    if all_schemes:
        keys = all_schemes[0].keys()
        with open('schemes_data.csv', 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_schemes)
            
    print("Export complete: schemes_data.csv and schemes_data.json have been saved.")

if __name__ == "__main__":
    start = time.time()
    main()
    print(f"Finished in {time.time() - start:.2f} seconds.")
