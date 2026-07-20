"""
Configuration file for Portal Pass automation tests.

Settings for:
- Admin and User portal URLs
- Test credentials (email/password)
- Browser headless/headed mode (CI/CD aware)
- Timeouts
"""

import os

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================
# Detect CI/CD environment
IS_CI = os.getenv("CI", "").lower() in ["true", "1"]
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS", "").lower() in ["true", "1"]
IS_LOCAL = not IS_CI

# ============================================================================
# ADMIN PORTAL CONFIGURATION
# ============================================================================
ADMIN_BASE_URL = (
    os.getenv("PORTAL_ADMIN_BASE_URL", "").strip().rstrip("/")
    or "https://portal-pass-admin.weavers-web.com"
)
ADMIN_LOGIN_URL = f"{ADMIN_BASE_URL}/login"
ADMIN_DASHBOARD_URL = f"{ADMIN_BASE_URL}/dashboard"

# ============================================================================
# USER PORTAL CONFIGURATION
# ============================================================================
USER_BASE_URL = (
    os.getenv("PORTAL_USER_BASE_URL", "").strip().rstrip("/")
    or "https://portal-pass-web.weavers-web.com"
)

# ============================================================================
# TEST CREDENTIALS
# ============================================================================
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin.portal@yopmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin1234!")

# Optional: User credentials (if needed for future user login tests)
USER_EMAIL = os.getenv("USER_EMAIL", "user@portal-pass.com")
USER_PASSWORD = os.getenv("USER_PASSWORD", "User1234!")

# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================
# Headless mode: True for CI/CD, False for local debugging
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "").lower()

if PLAYWRIGHT_HEADLESS in ["true", "1"]:
    HEADLESS = True
elif PLAYWRIGHT_HEADLESS in ["false", "0"]:
    HEADLESS = False
else:
    # Default: headless in CI/CD, headed locally
    HEADLESS = IS_CI or not os.environ.get("DISPLAY")

# Viewport settings
VIEWPORT_WIDTH = int(os.getenv("VIEWPORT_WIDTH", "1920"))
VIEWPORT_HEIGHT = int(os.getenv("VIEWPORT_HEIGHT", "1080"))
VIEWPORT = {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}

# Browser launch args
BROWSER_ARGS = []
if not HEADLESS:
    BROWSER_ARGS.append("--start-maximized")

# ============================================================================
# TIMEOUT CONFIGURATION (in milliseconds)
# ============================================================================
# Navigation timeout
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", "40000"))

# Selector wait timeout
SELECTOR_TIMEOUT = int(os.getenv("SELECTOR_TIMEOUT", "25000"))

# URL wait timeout
URL_WAIT_TIMEOUT = int(os.getenv("URL_WAIT_TIMEOUT", "20000"))

# Element visibility timeout
VISIBILITY_TIMEOUT = int(os.getenv("VISIBILITY_TIMEOUT", "20000"))

# Generic page timeout for transitions
PAGE_WAIT_TIMEOUT = int(os.getenv("PAGE_WAIT_TIMEOUT", "1000"))

# Login flow timeout
LOGIN_TIMEOUT = int(os.getenv("LOGIN_TIMEOUT", "15000"))

# ============================================================================
# FEATURE FLAGS
# ============================================================================
# Enable/disable screenshot capture for failed tests (default: True)
SCREENSHOT_ON_FAIL = os.getenv("SCREENSHOT_ON_FAIL", "true").lower() in ["true", "1"]

# Enable/disable video recording
VIDEO_RECORDING = os.getenv("VIDEO_RECORDING", "false").lower() in ["true", "1"]

# ============================================================================
# LOGGING & REPORTING
# ============================================================================
# Report directory
REPORT_DIR = os.getenv("REPORT_DIR", "reports")
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "screenshots")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def print_config():
    """Print current configuration for debugging."""
    print("\n" + "=" * 70)
    print("PORTAL PASS AUTOMATION CONFIGURATION")
    print("=" * 70)
    print(f"Environment: {'CI/CD' if IS_CI else 'LOCAL'}")
    print(f"Admin URL: {ADMIN_BASE_URL}")
    print(f"User URL: {USER_BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print(f"Headless: {HEADLESS}")
    print(f"Viewport: {VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}")
    print(f"Navigation Timeout: {NAVIGATION_TIMEOUT}ms")
    print(f"Selector Timeout: {SELECTOR_TIMEOUT}ms")
    print(f"Screenshot on Fail: {SCREENSHOT_ON_FAIL}")
    print("=" * 70 + "\n")
