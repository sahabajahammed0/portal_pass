import json
import os

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


@pytest.fixture
def delete_category_data():
    with open("data/delete_category.json", "r") as file:
        return json.load(file)["categories"]