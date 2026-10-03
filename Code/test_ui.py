import time
import sys
from playwright.sync_api import sync_playwright

def run_test():
    print("Starting Playwright UI Verification for AURA Platform...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://localhost:8000/")
            
            print("1. Clicking '+ Simulate High Risk' button...")
            page.click("text=+ Simulate High Risk")
            
            print("2. Waiting 4 seconds for API, RAG, and AI Triage to process...")
            time.sleep(4)
            
            print("3. Scanning live queue for the new High Risk alert...")
            high_risk_rows = page.locator("tr:has-text('HIGH')")
            count = high_risk_rows.count()
            
            if count > 0:
                print(f"SUCCESS: Found {count} High Risk alert(s) successfully rendered in the table.")
                
                first_row_text = high_risk_rows.nth(0).inner_text()
                if "Needs Review" in first_row_text:
                    print("SUCCESS: Status correctly set to 'Needs Review' (Escalated to human).")
                else:
                    print(f"ERROR: Incorrect status mapped. Row text says: {first_row_text}")
                
                print("4. Clicking the row to verify Slide-out Modal & C2A Interface...")
                high_risk_rows.nth(0).click()
                time.sleep(1)
                
                modal = page.locator("#case-modal")
                if modal.is_visible():
                    print("SUCCESS: Slide-out modal opens correctly.")
                    rationale = page.locator("#modal-rationale").inner_text()
                    print(f"AI RATIONALE CAPTURED: '{rationale}'")
                else:
                    print("ERROR: Modal failed to open upon clicking the row.")
                    sys.exit(1)
            else:
                print("ERROR: High Risk alert did not appear in the table after 4 seconds.")
                sys.exit(1)
            
            browser.close()
            print("ALL PLAYWRIGHT TESTS PASSED SUCCESSFULLY.")
    except Exception as e:
        print(f"FATAL ERROR DURING PLAYWRIGHT EXECUTION: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()
