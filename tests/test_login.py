from pages.login_page import LoginPage


def test_login(page):
    login = LoginPage(page)

    login.sign_in_to_be_visiable()
    login.forgot_password_btn_visiable()
    login.login("admin.portal@yopmail.com", "Admin1234!")
    login.forgot_password_btn_visiable()
    login.admin_dashboard_visable()
    
    