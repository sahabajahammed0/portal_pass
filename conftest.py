import pytest
import json
import os
import re
from datetime import datetime
from playwright.sync_api import expect, sync_playwright

from pages.admin.login_page import LoginPage
from pages.admin.category_management import CategoryManagement
from pages.admin.dashboard_page import DashboardPage
from pages.admin.event_creation_page import EventCreationPage
from pages.admin.place_listing_page import PlaceListing
from config import (
    ADMIN_BASE_URL, ADMIN_LOGIN_URL, ADMIN_DASHBOARD_URL, ADMIN_EMAIL, ADMIN_PASSWORD,
    USER_BASE_URL, HEADLESS, VIEWPORT, BROWSER_ARGS, NAVIGATION_TIMEOUT,
    SELECTOR_TIMEOUT, URL_WAIT_TIMEOUT, VISIBILITY_TIMEOUT, PAGE_WAIT_TIMEOUT,
    IS_CI, SCREENSHOT_ON_FAIL, print_config
)

# Absolute path to conftest.py's directory for robust path resolution on any machine
CONFTEST_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(CONFTEST_DIR, "state.json")
DEFAULT_ADMIN_BASE_URL = "https://portal-pass-admin.weavers-web.com"
# Set PORTAL_ADMIN_BASE_URL in CI to an approved staging/test hostname that is
# allowlisted in Cloudflare.  An empty GitHub Actions variable safely falls
# back to the existing production URL for local runs.
ADMIN_BASE_URL = os.getenv("PORTAL_ADMIN_BASE_URL", DEFAULT_ADMIN_BASE_URL).strip().rstrip("/") or DEFAULT_ADMIN_BASE_URL
LOGIN_URL = f"{ADMIN_BASE_URL}/login"
DASHBOARD_URL = f"{ADMIN_BASE_URL}/dashboard"

@pytest.fixture(scope="session")
def shared_page(playwright):
    """
    Session-scoped page fixture for local runs.
    Logs in once and holds authentication state across the entire test session.
    """
    headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()
    if headless_env in ["true", "1"]:
        headless = True
    elif headless_env in ["false", "0"]:
        headless = False
    else:
        headless = not os.environ.get("DISPLAY")

    print("\n🔑 [Local Run] Launching shared browser session...")
    if headless:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
    else:
        browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)

    page = context.new_page()
    try:
        for attempt in range(1, 3):
            try:
                
                page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)
                page.wait_for_selector("[data-testid='login-email-input']", timeout=25000)

                page.get_by_test_id("login-email-input").fill("admin.portal@yopmail.com")
                page.get_by_test_id("login-password-input").fill("Admin1234!")
                page.get_by_test_id("login-submit-btn").click()

                page.wait_for_url("**/dashboard**", timeout=20000)
                expect(page.get_by_role("link", name="Event Repository")).to_be_visible(timeout=20000)
                print("💾 [Local Run] Shared session authenticated successfully.")
                break
            except Exception as error:
                print(f"⚠️ [Local Run] Login attempt {attempt}/2 failed: {error}")
                if attempt == 2:
                    raise

        yield page

    finally:
        page.close()
        context.close()
        browser.close()


@pytest.fixture
def page(request, playwright):
    """
    Function-scoped page fixture.
    - In CI/CD: Performs a fresh login for every test to bypass Cloudflare cookie reuse detection.
    - Locally: Reuses the session-scoped page for optimal execution speed and holding authentication state.
    """
    if os.getenv("CI") == "true":
        # Fresh login for CI/CD environments
        headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()
        if headless_env in ["true", "1"]:
            headless = True
        elif headless_env in ["false", "0"]:
            headless = False
        else:
            headless = not os.environ.get("DISPLAY")
        
        print("\n🔑 [CI Run] Launching isolated browser instance and performing login...")
        if headless:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
        else:
            browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)

        page_inst = context.new_page()
        try:
            for attempt in range(1, 3):
                try:
                    page_inst.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=40000)
                    page_inst.wait_for_selector("[data-testid='login-email-input']", timeout=25000)

                    page_inst.get_by_test_id("login-email-input").fill("admin.portal@yopmail.com")
                    page_inst.get_by_test_id("login-password-input").fill("Admin1234!")
                    page_inst.get_by_test_id("login-submit-btn").click()

                    page_inst.wait_for_url("**/dashboard**", timeout=20000)
                    expect(page_inst.get_by_role("link", name="Event Repository")).to_be_visible(timeout=20000)
                    print("💾 [CI Run] Authenticated successfully.")
                    break
                except Exception as error:
                    print(f"⚠️ [CI Run] Login attempt {attempt}/2 failed: {error}")
                    if attempt == 2:
                        try:
                            page_inst.screenshot(path="debug_login_page.png", full_page=True)
                            with open("debug_login_page.html", "w", encoding="utf-8") as f:
                                f.write(page_inst.content())
                        except Exception:
                            pass
                        raise

            yield page_inst

        finally:
            page_inst.close()
            context.close()
            browser.close()
    else:
        # Local run: Retrieve the shared, authenticated page
        shared_p = request.getfixturevalue("shared_page")
        
        # Navigate back to dashboard if we are not there
        if not shared_p.url.startswith(ADMIN_BASE_URL):
            shared_p.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=30000)
        else:
            try:
                shared_p.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=20000)
            except Exception:
                shared_p.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)

        expect(shared_p.get_by_role("link", name="Event Repository")).to_be_visible(timeout=20000)
        yield shared_p


@pytest.fixture
def user_page(playwright):
    """
    Function-scoped page fixture for testing the public/user-facing portal.
    Does NOT authenticate; opens the public user portal directly.
    """
    headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()
    if headless_env in ["true", "1"]:
        headless = True
    elif headless_env in ["false", "0"]:
        headless = False
    else:
        headless = not os.environ.get("DISPLAY")

    print("\n🌍 [User Portal] Launching browser for public/user portal...")
    # Use Denver, CO coordinates as default to display regional events
    geo_location = {"latitude": 39.7392, "longitude": -104.9903}
    permissions = ["geolocation"]

    if headless:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            geolocation=geo_location,
            permissions=permissions
        )
    else:
        browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(
            no_viewport=True,
            geolocation=geo_location,
            permissions=permissions
        )

    context.grant_permissions(["geolocation"], origin="https://portal-pass-web.weavers-web.com")
    user_p = context.new_page()
    yield user_p

    user_p.close()
    context.close()
    browser.close()


@pytest.fixture
def user_portal_browser(playwright):
    """
    Factory fixture that creates a dedicated, isolated browser instance for the User Portal.
    Use this instead of page.context.new_page() when a test needs to open the User Portal
    while also operating the Admin Portal — this ensures Cloudflare sees a fresh real browser
    (not a tab inside the admin context which has no user portal clearance).

    Usage:
        def test_something(user_portal_browser, user_viewport):
            user_p = user_portal_browser(user_viewport["width"], user_viewport["height"])
            user_event_page = UserEventPage(user_p)
            user_event_page.navigate_directly_to_events()
            ...
            user_p.close()  # Always close when done
    """
    headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()
    if headless_env in ["true", "1"]:
        headless = True
    elif headless_env in ["false", "0"]:
        headless = False
    else:
        headless = not os.environ.get("DISPLAY")

    geo_location = {"latitude": 39.7392, "longitude": -104.9903}
    permissions = ["geolocation"]
    created = []  # track all opened resources for cleanup

    def _factory(width: int = 1920, height: int = 1080):
        if headless:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": width, "height": height},
                geolocation=geo_location,
                permissions=permissions
            )
        else:
            browser = playwright.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(
                no_viewport=True,
                geolocation=geo_location,
                permissions=permissions
            )
        context.grant_permissions(["geolocation"], origin="https://portal-pass-web.weavers-web.com")
        p = context.new_page()
        created.append((p, context, browser))
        return p

    yield _factory

    # Cleanup all browser instances created during the test
    for p, context, browser in created:
        try:
            p.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass
        try:
            browser.close()
        except Exception:
            pass



@pytest.fixture
def login_page(page):
    return LoginPage(page)


@pytest.fixture
def category_page(page):
    return CategoryManagement(page)


@pytest.fixture
def dashboard_page(page):
    return DashboardPage(page)


@pytest.fixture
def event_creation_page(page):
    return EventCreationPage(page)


@pytest.fixture
def place_listing_page(page):
    return PlaceListing(page)


@pytest.fixture
def event_repo(dashboard_page):
    """
    Automatically navigates to the Event Repository page.
    """
    dashboard_page.click_event_reporsitory()
    dashboard_page.page.wait_for_timeout(1000)
    return dashboard_page


@pytest.fixture
def category_data():
    data_path = os.path.join(CONFTEST_DIR, "data", "category.json")
    with open(data_path, "r") as file:
        data = json.load(file)
    return data["categories"]


@pytest.fixture
def edit_category_data():
    data_path = os.path.join(CONFTEST_DIR, "data", "edit_category.json")
    with open(data_path, "r") as file:
        return json.load(file)["categories"]
    
# Screenshot capture and Allure report integration

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        page = item.funcargs.get("page") if hasattr(item, "funcargs") else None
        
        # Capture diagnostic screenshots only when a test fails.
        if report.failed and SCREENSHOT_ON_FAIL:
            screenshots_dir = os.path.join(os.getcwd(), "screenshots", "failed")
        else:
            screenshots_dir = None
        
        # Capture screenshot if page is available
        if page is not None and screenshots_dir:
            os.makedirs(screenshots_dir, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.name)
            screenshot_path = os.path.join(screenshots_dir, f"{safe_name}.png")
            
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved: {screenshot_path}")
                try:
                    import allure
                    with open(screenshot_path, "rb") as img:
                        allure.attach(
                            img.read(),
                            name=f"{safe_name}_screenshot",
                            attachment_type=allure.attachment_type.PNG
                        )
                except ImportError:
                    pass
            except Exception as e:
                print(f"⚠️ Could not capture screenshot: {e}")

@pytest.fixture
def delete_category_data():
    data_path = os.path.join(CONFTEST_DIR, "data", "delete_category.json")
    with open(data_path, "r") as file:
        return json.load(file)["categories"]

@pytest.fixture
def place_listing_data():
    data_path = os.path.join(CONFTEST_DIR, "data", "place_listing.json")
    with open(data_path, "r") as file:
        return json.load(file)["places"]


def pytest_sessionfinish(session, exitstatus):
    """
    Automatically serves the Allure report locally after the entire test suite completes.
    Skipped in CI/CD environments to prevent blocking pipeline execution.
    """
    import os
    import subprocess

    if os.getenv("CI") == "true" or os.getenv("NO_SERVE") == "true":
        print("\n⏭️ Skipping Allure report auto-serve.")
        return

    print("\n📊 Test execution complete. Launching Allure report server...")
    try:
        # Run 'allure serve allure-results'
        subprocess.run(["allure", "serve", "allure-results"])
    except Exception as e:
        print(f"⚠️ Failed to launch Allure report server: {e}")

