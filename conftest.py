import pytest,json
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.category_management import CategoryManagement
from pages.dashboard_page import DashboardPage


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://portal-pass-admin.weavers-web.com/login")  # Replace with your application's URL

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