import json
import os
import re

import pytest
from playwright.sync_api import sync_playwright

from pages.admin.login_page import LoginPage
from pages.admin.category_management import CategoryManagement
from pages.admin.dashboard_page import DashboardPage
from pages.admin.event_creation_page import EventCreationPage


@pytest.fixture(scope="function")
def page():
    ci = os.getenv("CI", "false").lower() == "true"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=ci,
            args=[] if ci else ["--start-maximized"]
        )

        if ci:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
        else:
            page = browser.new_page(no_viewport=True)

        page.goto("https://portal-pass-admin.weavers-web.com/login", wait_until="networkidle")

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
def category_data():
    with open("data/category.json", "r") as file:
        data = json.load(file)
    return data["categories"]


@pytest.fixture
def edit_category_data():
    with open("data/edit_category.json", "r") as file:
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
    with open("data/delete_category.json", "r") as file:
        return json.load(file)["categories"]