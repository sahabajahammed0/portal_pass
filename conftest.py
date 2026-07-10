import pytest
import json
import os
from playwright.sync_api import sync_playwright
from pages.admin.login_page import LoginPage
from pages.admin.category_management import CategoryManagement
from pages.admin.dashboard_page import DashboardPage
from pages.admin.event_creation_page import EventCreationPage

# Path for saving session state
STATE_FILE = os.path.abspath("state.json")


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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        # Load the stored authentication state
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
    with open("data/category.json", "r") as file:
        data = json.load(file)

    return data["categories"]


@pytest.fixture
def edit_category_data():
    with open("data/edit_category.json") as file:
        return json.load(file)["categories"]


@pytest.fixture
def delete_category_data():
    with open("data/delete_category.json") as file:
        return json.load(file)["categories"]