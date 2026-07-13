import pytest
import json
import os
import re
from playwright.sync_api import sync_playwright

from pages.admin.login_page import LoginPage
from pages.admin.category_management import CategoryManagement
from pages.admin.dashboard_page import DashboardPage
from pages.admin.event_creation_page import EventCreationPage

# Absolute path to conftest.py's directory for robust path resolution on any machine
CONFTEST_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(CONFTEST_DIR, "state.json")


@pytest.fixture(scope="session")
def auth_state():
    """
    Session-scoped fixture to perform login once and save authentication state.
    """
    with sync_playwright() as p:
        print("\n🔑 Performing session login to capture authentication state...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://portal-pass-admin.weavers-web.com/login")
        
        # Log in
        page.get_by_test_id("login-email-input").fill("admin.portal@yopmail.com")
        page.get_by_test_id("login-password-input").fill("Admin1234!")
        page.get_by_test_id("login-submit-btn").click()
        
        # Wait for the dashboard to confirm auth was successful
        page.wait_for_selector("text=Admin Dashboard", timeout=15000)
        
        # Save storage state
        context.storage_state(path=STATE_FILE)
        print("💾 Authentication state saved successfully.")
        browser.close()
        
    yield STATE_FILE
    
    # Cleanup state file after session finishes
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
            print("🗑️ Cleaned up authentication state file.")
        except Exception:
            pass


@pytest.fixture
def page(auth_state):
    """
    Function-scoped page fixture that reuses the captured session state.
    """
    # Detect headless mode dynamically: check environment variable, fallback to True if no graphical display is present
    headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()
    if headless_env in ["true", "1"]:
        headless = True
    elif headless_env in ["false", "0"]:
        headless = False
    else:
        # Fallback to headless on Linux if DISPLAY is not set (e.g. CI/CD or headless server)
        headless = not os.environ.get("DISPLAY")

    with sync_playwright() as p:
        if headless:
            browser = p.chromium.launch(headless=True)
            # Set a standard high-resolution viewport for headless runs to ensure consistent layout
            context = browser.new_context(viewport={"width": 1920, "height": 1080}, storage_state=auth_state)
        else:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True, storage_state=auth_state)

        page = context.new_page()
        # Direct navigation to dashboard (bypass login page)
        page.goto("https://portal-pass-admin.weavers-web.com/dashboard")

        yield page

        browser.close()


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
    
# Screenshot if test case failed  it should automatic captured Screenshot/failed folder 

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page") if hasattr(item, "funcargs") else None
        if page is not None:
            screenshots_dir = os.path.join(os.getcwd(), "screenshots", "failed")
            os.makedirs(screenshots_dir, exist_ok=True)

            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.name)
            screenshot_path = os.path.join(screenshots_dir, f"{safe_name}.png")

            try:
                page.screenshot(path=screenshot_path, full_page=True)
            except Exception:
                pass

@pytest.fixture
def delete_category_data():
    data_path = os.path.join(CONFTEST_DIR, "data", "delete_category.json")
    with open(data_path, "r") as file:
        return json.load(file)["categories"]