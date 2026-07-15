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
def auth_state():
    """
    Session-scoped fixture to perform login and save authentication state.

    The public admin app is served behind a CDN.  A transient failed asset or
    bot-challenge request can leave the SPA root empty in CI; retrying in a new
    context is materially different from repeatedly waiting in the broken one.
    """
    with sync_playwright() as p:
        print("\n🔑 Performing session login to capture authentication state...")
        browser = p.chromium.launch(headless=True)
        page = None
        last_error = None

        try:
            for attempt in range(1, 3):
                context = browser.new_context()
                page = context.new_page()
                diagnostics = []

                def record_console(message):
                    if message.type in {"error", "warning"}:
                        diagnostics.append(f"console {message.type}: {message.text}")

                def record_response(response):
                    if response.status >= 400:
                        diagnostics.append(f"HTTP {response.status}: {response.url}")

                page.on("console", record_console)
                page.on("pageerror", lambda error: diagnostics.append(f"page error: {error}"))
                page.on("response", record_response)
                try:
                    # Do not wait for the browser's ``load`` event here.  The admin SPA
                    # loads third-party/long-lived resources in CI, which can keep that
                    # event pending even though the login form is already interactive.
                    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_selector("[data-testid='login-email-input']", timeout=25000)

                    page.get_by_test_id("login-email-input").fill("admin.portal@yopmail.com", timeout=15000)
                    page.get_by_test_id("login-password-input").fill("Admin1234!", timeout=15000)
                    page.get_by_test_id("login-submit-btn").click(timeout=15000)

                    # Confirm the actual route and navigation used by the test suite.
                    # The dashboard title is presentation text and has changed before;
                    # the Event Repository link is a stable authenticated-page control.
                    page.wait_for_url("**/dashboard**", timeout=20000)
                    expect(page.get_by_role("link", name="Event Repository")).to_be_visible(timeout=20000)

                    context.storage_state(path=STATE_FILE)
                    print("💾 Authentication state saved successfully.")
                    break
                except Exception as error:
                    last_error = error
                    try:
                        body_text = page.locator("body").inner_text(timeout=2000)
                        print(
                            "⚠️ Login bootstrap diagnostics: "
                            f"url={page.url!r}; title={page.title()!r}; "
                            f"body={body_text[:500].replace(chr(10), ' ')!r}"
                        )
                        for message in diagnostics[:10]:
                            print(f"   {message}")
                    except Exception as diagnostic_error:
                        print(f"⚠️ Could not collect login diagnostics: {diagnostic_error}")
                    if attempt == 2:
                        raise
                    print(f"⚠️ Login page did not initialize (attempt {attempt}/2); retrying with a fresh context...")
                finally:
                    if last_error is not None and attempt < 2:
                        context.close()

        except Exception as e:
            # Save debug artifacts so the GitHub "Debug-Login-Page" upload step has real content
            print(f"❌ Login failed: {e}")
            try:
                page.screenshot(path="debug_login_page.png", full_page=True)
                with open("debug_login_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("🛠️  Debug screenshot and HTML saved for CI inspection.")
            except Exception as debug_err:
                print(f"⚠️  Could not save debug artifacts: {debug_err}")
            raise  # Re-raise so pytest marks the setup as ERROR

        finally:
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
        # Direct navigation to dashboard (bypass login page).  As above, do not
        # wait for all background resources to finish loading.
        page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=60000)
        expect(page.get_by_role("link", name="Event Repository")).to_be_visible(timeout=30000)

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
