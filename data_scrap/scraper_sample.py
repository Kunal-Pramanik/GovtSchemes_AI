import requests
import json
import csv
from bs4 import BeautifulSoup
import time

API_KEY = "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'x-api-key': API_KEY,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0)',
    'origin': 'https://www.myscheme.gov.in',
    'referer': 'https://www.myscheme.gov.in/'
}

def strip_html(html_data):
    if not html_data: return ""
    if isinstance(html_data, list):
        cleaned = []
        for item in html_data:
            if isinstance(item, str): cleaned.append(BeautifulSoup(item, "html.parser").get_text(separator=' ', strip=True))
            elif isinstance(item, dict):
                content = item.get('content', '') or item.get('details', '') or str(item)
                cleaned.append(BeautifulSoup(content, "html.parser").get_text(separator=' ', strip=True))
        return "\n".join(cleaned)
    elif isinstance(html_data, str):
        return BeautifulSoup(html_data, "html.parser").get_text(separator=' ', strip=True)
    return str(html_data)

def main():
    print("Fetching first 10 schemes as a sample...")
    # Delay to respect 429
    time.sleep(3)
    try:
        r = requests.get("https://api.myscheme.gov.in/search/v6/schemes?lang=en&from=0&size=10&q=%5B%5D&keyword=&sort=", headers=HEADERS)
        items = r.json()['data']['hits']['items']
    except Exception as e:
        print("Failed to get basic data:", e)
        return

    all_schemes = []
    for item in items:
        slug = item['fields']['slug']
        basic = item['fields']
        try:
            r_det = requests.get(f"https://api.myscheme.gov.in/schemes/v6/public/schemes?slug={slug}&lang=en", headers=HEADERS)
            time.sleep(0.5)
            if r_det.status_code == 200:
                data = r_det.json()['data']['en']
                details_str = data.get('schemeContent', {}).get('detailedDescription', '')
                if not details_str: details_str = data.get('schemeContent', {}).get('briefDescription', '')
                benefits_list = data.get('schemeContent', {}).get('benefits', [])
                
                eligibility = data.get('eligibilityCriteria', {}).get('description', '')
                if not eligibility:
                    criteria_rules = data.get('eligibilityCriteria', {}).get('rules', [])
                    eligibility = "\n".join([str(x) for x in criteria_rules])

                app_process = data.get('applicationProcess', [])
                app_str = ""
                for mode in app_process:
                    mode_name = mode.get('mode', 'Process')
                    steps = mode.get('process', [])
                    app_str += f"{mode_name}:\n"
                    for s in steps: app_str += f"- {s.get('text', '')}\n"
                        
                all_schemes.append({
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
                })
        except Exception as e:
            pass
            
    print("Done. Saving sample...")
    if all_schemes:
        keys = all_schemes[0].keys()
        with open('sample_schemes.csv', 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_schemes)
    print("Sample CSV ready.")

if __name__ == "__main__":
    main()
