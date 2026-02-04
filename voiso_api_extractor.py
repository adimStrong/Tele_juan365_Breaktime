"""
Voiso API Key Extractor
Automates login and API key extraction from Voiso dashboard
With screenshots at each step for debugging
"""

import os
import getpass
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Paths
SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots"

def setup_directories():
    """Create required directories"""
    SCREENSHOTS_DIR.mkdir(exist_ok=True)

def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars

def save_to_env(key, value):
    """Save or update a key-value pair in .env file"""
    env_vars = load_env()
    env_vars[key] = value

    with open(ENV_FILE, 'w') as f:
        for k, v in env_vars.items():
            f.write(f'{k}="{v}"\n')
    print(f"  [SAVED] {key} to {ENV_FILE}")

def mask_key(key):
    """Mask API key for display"""
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

def take_screenshot(page, step_name):
    """Take a screenshot with timestamp"""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = SCREENSHOTS_DIR / f"{timestamp}_{step_name}.png"
    page.screenshot(path=str(filename), full_page=True)
    print(f"  [SCREENSHOT] Saved: {filename.name}")
    return filename

def get_credentials():
    """Get Voiso credentials from .env or user input"""
    env_vars = load_env()

    voiso_url = env_vars.get('VOISO_URL', '')
    voiso_email = env_vars.get('VOISO_EMAIL', '')
    voiso_password = env_vars.get('VOISO_PASSWORD', '')

    print("\n" + "="*60)
    print("        VOISO API KEY EXTRACTOR")
    print("="*60 + "\n")

    # URL
    if not voiso_url:
        print("Enter your Voiso URL")
        print("  Format: https://[CLUSTER_ID].voiso.com")
        print("  Example: https://abc123.voiso.com")
        voiso_url = input("\n  URL: ").strip()
        if not voiso_url.startswith('http'):
            voiso_url = 'https://' + voiso_url
    else:
        print(f"[OK] Using URL from .env: {voiso_url}")

    # Email
    if not voiso_email:
        voiso_email = input("\nEnter your Voiso email: ").strip()
    else:
        print(f"[OK] Using email from .env: {voiso_email}")

    # Password
    if not voiso_password:
        voiso_password = getpass.getpass("\nEnter your Voiso password: ")
    else:
        print("[OK] Using password from .env")

    # Offer to save credentials
    if 'VOISO_URL' not in env_vars:
        print("\n" + "-"*40)
        save_creds = input("Save credentials to .env for future use? (y/n): ").lower().strip()
        if save_creds == 'y':
            save_to_env('VOISO_URL', voiso_url)
            save_to_env('VOISO_EMAIL', voiso_email)
            save_pass = input("Also save password? (y/n): ").lower().strip()
            if save_pass == 'y':
                save_to_env('VOISO_PASSWORD', voiso_password)
        print("-"*40)

    return voiso_url, voiso_email, voiso_password

def wait_and_check(page, timeout=5000):
    """Wait for network to be idle"""
    try:
        page.wait_for_load_state('networkidle', timeout=timeout)
    except:
        pass
    page.wait_for_timeout(1000)

def extract_api_key():
    """Main function to extract Voiso API key"""
    setup_directories()
    voiso_url, email, password = get_credentials()

    with sync_playwright() as p:
        print("\n[STEP 1] Launching browser...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500  # Slow down for visibility
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # ===== STEP 2: Navigate to login =====
            print("\n[STEP 2] Navigating to Voiso login...")
            page.goto(voiso_url, wait_until='domcontentloaded', timeout=30000)
            wait_and_check(page)
            take_screenshot(page, "01_login_page")

            # ===== STEP 3: Fill email =====
            print("\n[STEP 3] Looking for email field...")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[autocomplete="email"]',
                '#email',
                'input[name="username"]',
                'input[type="text"]',  # Fallback
            ]

            email_filled = False
            for selector in email_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=2000):
                        field.click()
                        field.fill(email)
                        email_filled = True
                        print(f"  [OK] Email entered using: {selector}")
                        break
                except:
                    continue

            if not email_filled:
                take_screenshot(page, "02_email_not_found")
                print("  [MANUAL] Could not find email field automatically.")
                input("  Please enter your email manually, then press Enter...")

            take_screenshot(page, "02_email_entered")

            # ===== STEP 4: Fill password =====
            print("\n[STEP 4] Looking for password field...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '#password',
                'input[autocomplete="current-password"]',
            ]

            password_filled = False
            for selector in password_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=2000):
                        field.click()
                        field.fill(password)
                        password_filled = True
                        print(f"  [OK] Password entered using: {selector}")
                        break
                except:
                    continue

            if not password_filled:
                take_screenshot(page, "03_password_not_found")
                print("  [MANUAL] Could not find password field automatically.")
                input("  Please enter your password manually, then press Enter...")

            take_screenshot(page, "03_password_entered")

            # ===== STEP 5: Click login button =====
            print("\n[STEP 5] Looking for login button...")
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Submit")',
                'input[type="submit"]',
                '[data-testid*="login" i]',
            ]

            login_clicked = False
            for selector in login_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        login_clicked = True
                        print(f"  [OK] Clicked login button: {selector}")
                        break
                except:
                    continue

            if not login_clicked:
                take_screenshot(page, "04_login_button_not_found")
                print("  [MANUAL] Could not find login button automatically.")
                input("  Please click the login button manually, then press Enter...")

            wait_and_check(page, 10000)
            take_screenshot(page, "04_after_login_click")

            # ===== STEP 6: Handle 2FA =====
            print("\n[STEP 6] Checking for 2FA...")
            print("  " + "="*50)
            print("  |  IF YOU SEE A 2FA/OTP SCREEN:              |")
            print("  |  Complete the verification in the browser  |")
            print("  " + "="*50)

            take_screenshot(page, "05_2fa_check")

            input("\n  Press Enter once you're logged in and see the dashboard...")

            wait_and_check(page)
            take_screenshot(page, "06_dashboard")

            # ===== STEP 7: Navigate to Users =====
            print("\n[STEP 7] Navigating to Users section...")

            # First try clicking the Users menu
            users_selectors = [
                'a[href*="users"]',
                'a:has-text("Users")',
                'span:has-text("Users")',
                '[data-menu*="users" i]',
                '.sidebar-item:has-text("Users")',
                'li:has-text("Users") a',
            ]

            users_found = False
            for selector in users_selectors:
                try:
                    menu = page.locator(selector).first
                    if menu.is_visible(timeout=3000):
                        menu.click()
                        users_found = True
                        print(f"  [OK] Clicked: {selector}")
                        break
                except:
                    continue

            if not users_found:
                # Try direct URL patterns
                print("  Trying direct URL navigation...")
                urls_to_try = [
                    f"{voiso_url}/users",
                    f"{voiso_url}/#/users",
                    f"{voiso_url}/admin/users",
                    f"{voiso_url}/settings/users",
                    f"{voiso_url}/#/admin/users",
                ]

                for url in urls_to_try:
                    try:
                        print(f"    Trying: {url}")
                        page.goto(url, wait_until='domcontentloaded', timeout=10000)
                        wait_and_check(page)
                        # Check if we landed on users page
                        if 'user' in page.url.lower():
                            users_found = True
                            print(f"  [OK] Navigated to: {page.url}")
                            break
                    except:
                        continue

            if not users_found:
                take_screenshot(page, "07_users_not_found")
                print("\n  [MANUAL] Could not find Users section automatically.")
                print("  Please navigate to: Users > Users in the menu")
                input("  Press Enter when you're on the Users list page...")

            wait_and_check(page)
            take_screenshot(page, "07_users_page")

            # ===== STEP 8: Find and click user profile =====
            print("\n[STEP 8] Looking for your user profile...")
            print(f"  Searching for: {email}")

            user_selectors = [
                f'tr:has-text("{email}")',
                f'td:has-text("{email}")',
                f'a:has-text("{email}")',
                f'div:has-text("{email}")',
                f'[data-email="{email}"]',
            ]

            user_clicked = False
            for selector in user_selectors:
                try:
                    user = page.locator(selector).first
                    if user.is_visible(timeout=3000):
                        user.click()
                        user_clicked = True
                        print(f"  [OK] Found and clicked user profile")
                        break
                except:
                    continue

            if not user_clicked:
                take_screenshot(page, "08_user_not_found")
                print(f"\n  [MANUAL] Could not find profile for: {email}")
                print("  Please click on your user profile in the list.")
                input("  Press Enter when viewing your user details page...")

            wait_and_check(page)
            take_screenshot(page, "08_user_profile")

            # ===== STEP 9: Extract API Key =====
            print("\n[STEP 9] Searching for API Key...")

            api_key = None

            # Try various selectors for API key field
            api_key_selectors = [
                'input[name*="api" i][name*="key" i]',
                'input[id*="api" i][id*="key" i]',
                'input[name="apiKey"]',
                'input[name="api_key"]',
                '#apiKey',
                '#api_key',
                '#api-key',
                '[data-testid*="api" i]',
                'input[readonly]',
            ]

            for selector in api_key_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=2000):
                        value = field.get_attribute('value')
                        if value and len(value) > 10:  # Reasonable API key length
                            api_key = value
                            print(f"  [OK] Found API key with: {selector}")
                            break
                except:
                    continue

            # Try looking for API key label and nearby content
            if not api_key:
                try:
                    # Look for text containing "API" near an input
                    api_labels = page.locator('label:has-text("API"), div:has-text("API Key")')
                    count = api_labels.count()
                    for i in range(count):
                        label = api_labels.nth(i)
                        if label.is_visible():
                            # Try to find input in parent or sibling
                            parent = label.locator('xpath=..')
                            input_field = parent.locator('input').first
                            if input_field.is_visible():
                                value = input_field.get_attribute('value')
                                if value:
                                    api_key = value
                                    print("  [OK] Found API key near label")
                                    break
                except Exception as e:
                    print(f"  [DEBUG] Label search: {e}")

            take_screenshot(page, "09_api_key_search")

            if not api_key:
                print("\n  " + "="*50)
                print("  |  COULD NOT FIND API KEY AUTOMATICALLY        |")
                print("  |  Please locate the API Key on the page       |")
                print("  " + "="*50)
                print("\n  Look for a field labeled 'API Key', 'Token', etc.")
                api_key = input("\n  Enter the API Key you see: ").strip()

            # ===== STEP 10: Save API Key =====
            if api_key:
                print("\n[STEP 10] Saving API Key...")
                print("\n  " + "="*50)
                print("  |  API KEY EXTRACTED SUCCESSFULLY!             |")
                print("  " + "="*50)
                print(f"\n  API Key (masked): {mask_key(api_key)}")
                print(f"  Full length: {len(api_key)} characters")

                save_to_env('VOISO_API_KEY', api_key)

                take_screenshot(page, "10_success")

                print("\n  Your API key has been saved to .env file.")
                print(f"  Location: {ENV_FILE}")
            else:
                print("\n  [ERROR] No API key was captured.")
                take_screenshot(page, "10_failed")

        except PlaywrightTimeout as e:
            take_screenshot(page, "error_timeout")
            print(f"\n[ERROR] Timeout: {e}")
            print("  The page took too long to respond.")

        except Exception as e:
            try:
                take_screenshot(page, "error_exception")
            except:
                pass
            print(f"\n[ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\n" + "-"*60)
            print("Screenshots saved to:", SCREENSHOTS_DIR)
            print("Closing browser in 5 seconds...")
            print("-"*60)
            page.wait_for_timeout(5000)
            browser.close()

if __name__ == "__main__":
    extract_api_key()
