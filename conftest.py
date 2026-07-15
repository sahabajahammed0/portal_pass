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
# List to store test results for report generation
test_results = []


@pytest.fixture(scope="session")
def shared_page():
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

    with sync_playwright() as p:
        print("\n🔑 [Local Run] Launching shared browser session...")
        if headless:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
        else:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
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
def page(request):
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
        
        with sync_playwright() as p:
            print("\n🔑 [CI Run] Launching isolated browser instance and performing login...")
            if headless:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1920, "height": 1080})
            else:
                browser = p.chromium.launch(headless=False, args=["--start-maximized"])
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
    
# Screenshot capture and test report generation

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        page = item.funcargs.get("page") if hasattr(item, "funcargs") else None
        
        # Determine test status
        if report.failed:
            status = "FAILED"
            screenshots_dir = os.path.join(os.getcwd(), "screenshots", "failed")
        elif report.passed:
            status = "PASSED"
            screenshots_dir = os.path.join(os.getcwd(), "screenshots", "passed")
        else:
            status = "SKIPPED"
            screenshots_dir = None
        
        # Store result for report
        test_results.append({
            "name": item.name,
            "status": status,
            "duration": report.duration,
            "timestamp": datetime.now().isoformat()
        })
        
        # Capture screenshot if page is available
        if page is not None and screenshots_dir:
            os.makedirs(screenshots_dir, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", item.name)
            screenshot_path = os.path.join(screenshots_dir, f"{safe_name}.png")
            
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"⚠️ Could not capture screenshot: {e}")


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate test report at the end of the session."""
    import json
    
    # Create reports directory
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Count results
    passed = sum(1 for r in test_results if r["status"] == "PASSED")
    failed = sum(1 for r in test_results if r["status"] == "FAILED")
    skipped = sum(1 for r in test_results if r["status"] == "SKIPPED")
    total = len(test_results)
    
    # Create summary report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{(passed/total*100):.2f}%" if total > 0 else "0%"
        },
        "tests": test_results
    }
    
    # Save JSON report
    json_report_path = os.path.join(reports_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(json_report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"📊 JSON Report saved: {json_report_path}")
    
    # Generate HTML report
    html_report_path = os.path.join(reports_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    html_content = f"""
    <html>
    <head>
        <title>Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .passed {{ color: green; font-weight: bold; }}
            .failed {{ color: red; font-weight: bold; }}
            .skipped {{ color: orange; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
            th {{ background: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>🧪 Test Execution Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Timestamp:</strong> {report_data['timestamp']}</p>
            <p><strong>Total Tests:</strong> {total}</p>
            <p><strong>Passed:</strong> <span class="passed">{passed}</span></p>
            <p><strong>Failed:</strong> <span class="failed">{failed}</span></p>
            <p><strong>Skipped:</strong> <span class="skipped">{skipped}</span></p>
            <p><strong>Pass Rate:</strong> {report_data['summary']['pass_rate']}</p>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration (s)</th>
                <th>Timestamp</th>
            </tr>
    """
    
    for test in test_results:
        status_class = test["status"].lower()
        html_content += f"""
            <tr>
                <td>{test['name']}</td>
                <td><span class="{status_class}">{test['status']}</span></td>
                <td>{test['duration']:.2f}</td>
                <td>{test['timestamp']}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    with open(html_report_path, "w") as f:
        f.write(html_content)
    print(f"📊 HTML Report saved: {html_report_path}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("🎯 TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📈 Pass Rate: {report_data['summary']['pass_rate']}")
    print("="*60 + "\n")

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
