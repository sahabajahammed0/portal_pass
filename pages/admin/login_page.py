from playwright.sync_api import Page, expect

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.heading = page.get_by_role("heading", name="Operator Sign In")
        self.email = page.get_by_test_id("login-email-input")
        self.password = page.get_by_test_id("login-password-input")
        self.login_forgot_password = page.get_by_test_id("login-forgot-password-btn")
        self.Remember = page.get_by_text("Remember me")
        self.submit = page.get_by_test_id("login-submit-btn")
        self.Dashboard = page.get_by_role("heading", name="Admin Dashboard")

    # --- Actions ---
    
    def sign_in_to_be_visiable(self):
        # If already logged in (Dashboard heading is visible), skip this validation
        if self.Dashboard.is_visible():
            print("Already on Dashboard; skipping login sign-in visibility check.")
            return
        expect(self.heading).to_be_visible()

    def forgot_password_btn_visiable(self):
        # If already logged in, skip this validation
        if self.Dashboard.is_visible():
            print("Already on Dashboard; skipping forgot password button check.")
            return
        expect(self.login_forgot_password).to_be_visible()

    def admin_dashboard_visable(self):
        expect(self.Dashboard).to_be_visible()

    def enter_username(self, username):
        self.email.fill(username)

    def enter_password(self, password):
        self.password.fill(password)

    def login(self, username: str, password: str):
        # If already logged in, skip typing credentials and clicking submit
        if self.Dashboard.is_visible():
            print("Already authenticated; skipping credentials entry.")
            return
        self.enter_username(username)
        self.enter_password(password)
        self.submit.click()