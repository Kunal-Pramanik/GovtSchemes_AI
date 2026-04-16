from playwright.sync_api import sync_playwright
import json

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    
    headers = {}

    def handle_request(request):
        if "api.myscheme.gov.in" in request.url.lower():
            headers[request.url] = request.headers
            print(f"Captured headers for: {request.url}")

    page.on("request", handle_request)
    page.goto("https://www.myscheme.gov.in/search")
    
    # Wait for schemes to load
    page.wait_for_timeout(5000)
    
    browser.close()
    
    with open("headers.json", "w") as f:
        json.dump(headers, f, indent=2)

with sync_playwright() as playwright:
    run(playwright)
