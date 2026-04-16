from playwright.sync_api import sync_playwright
import json

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_responses = []

    # Listen to response events
    def handle_response(response):
        if "api" in response.url.lower() and response.status == 200:
            if "schemes" in response.url.lower() or "search" in response.url.lower():
                print(f"Intercepted API URL: {response.url}")
                try:
                    data = response.json()
                    api_responses.append({
                        "url": response.url,
                        "data": data
                    })
                    with open("intercepted.json", "w") as f:
                        json.dump(api_responses, f)
                except Exception as e:
                    pass

    page.on("response", handle_response)
    page.goto("https://www.myscheme.gov.in/search")
    
    # Wait for schemes to load
    page.wait_for_timeout(5000)
    
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
