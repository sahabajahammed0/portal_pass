# Portal Pass Test Automation Suite

A robust end-to-end (E2E) automated testing framework built using **Python**, **Pytest**, and **Playwright** utilizing the **Page Object Model (POM)** pattern. This suite validates key flows across both the **Admin Portal** and the public **User Portal**.

---

## 📋 Client Summary (What is Automated?)

This test suite ensures the quality, integrity, and stability of the Portal Pass platform by mimicking real user interactions. It tests the system end-to-end to verify that events and places created by administrators display correctly to end-users.

### Key Workflows Tested
1. **Event Creation & Validation (TC02, TC07)**:
   - Automated creation of events in the Admin portal using randomized mock data (dates, venues, contact information, descriptions, and media uploads).
   - Verifies that new events appear immediately in the Admin repository list with correct location, source, and status attributes.
2. **Dual-Status Toggling (TC06)**:
   - Validates event status switches in both directions:
     - **Inline switch toggle** directly from the repository list table (Active ➔ Inactive).
     - **Form toggle** from the Edit Event page (Inactive ➔ Active) using precise status controls.
3. **Multi-level Category & Date Filters (TC05)**:
   - Creates events under parent-child categories (e.g., `Sports ➔ Football`) and verifies that applying category and date-range filters on the User portal displays only matching events.
4. **Cross-Portal Event Visibility (TC04)**:
   - Validates the end-to-end flow: creating an event in the Admin Portal and instantly searching/verifying its details on the User Portal.
5. **Inactive Event Exclusion (User Portal)**:
   - Ensures that when an event is updated to **Inactive** in the Admin Portal, it immediately disappears from the User Portal search results to prevent customers from seeing inactive events.
6. **Public Portal Search & Sort**:
   - Tests navigation, footer links, sorting (A-Z and Z-A), and keyword searching on the public Events explore view.

---

## 🛠️ Developer & QA Guide (Technical Documentation)

### Technology Stack
- **Language**: Python 3.12+
- **Test Runner**: Pytest
- **Automation Driver**: Playwright (sync API)
- **Design Pattern**: Page Object Model (POM)
- **Reporting**: Allure Reports

### Project Structure
```text
portal_pass/
├── config.py              # Environment configuration & URLs
├── conftest.py            # Global fixtures (auth, page setups)
├── pytest.ini             # Pytest config (markers, timeouts, options)
├── requirements.txt       # Dependencies list
├── pages/                 # Page Objects (UI abstraction layer)
│   ├── admin/             # Admin Portal Page Objects
│   └── user_page/         # User Portal Page Objects
├── tests/                 # Test Suites
│   ├── admin/             # Admin flow tests (creation, status edit)
│   └── users/             # User portal flow tests (search, sort, filters)
└── data/                  # Mock data resources (images, etc.)
```

### Setup Instructions

1. **Clone the Repository** and navigate to the project directory:
   ```bash
   cd portal_pass
   ```

2. **Create and Activate a Python Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

---

### Executing Tests

#### Run All Tests (Local Mode)
To run the full suite using local authenticated session states (highly recommended for rapid local testing):
```bash
.venv/bin/pytest -v
```

#### Run All Tests (CI/CD Mode)
To bypass Cloudflare bot detection and run isolated fresh-login browser instances (simulating a clean CI pipeline):
```bash
CI=true .venv/bin/pytest -v
```

#### Run Specific Tests
- **Run Admin Portal Event Creation Suite**:
  ```bash
  .venv/bin/pytest -v tests/admin/test_event_creation.py
  ```
- **Run User Portal Event Suite**:
  ```bash
  .venv/bin/pytest -v tests/users/test_user_event.py
  ```

---

### Reporting (Allure Integration)

Test execution generates Allure-compatible results. To compile and view the report:

1. **Execute tests with Allure enabled**:
   ```bash
   .venv/bin/pytest --alluredir=allure-results
   ```
2. **Generate and open the report**:
   ```bash
   allure serve allure-results
   ```

---

### Key Framework Best Practices Implemented
- **Cloudflare Bypass**: Hybrid authentication fixture logic. Under CI mode (`CI=true`), it uses custom isolated fresh-login instances to bypass Cloudflare constraints, whereas local mode uses fast, serialized cookie-state storage.
- **No Hardcoded Dates**: All tests dynamically calculate dates relative to `datetime.now()` to ensure the suite is robust and can run infinitely on any calendar day.
- **Network-Level Sync**: Implements Playwright's `expect_response` listener to wait directly for backend API completion rather than arbitrary sleep timers, enhancing execution speed and test stability.
