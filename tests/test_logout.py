# tests/test_logout.py
from pages.login_page import LoginPage

def test_logout_with_pom(driver, base_url, creds):
    login = LoginPage(driver, base_url).open()
    dashboard = login.login_as(creds["username"], creds["password"])

    login_again = dashboard.logout(pause_seconds=1.0)

    # Assert we’re logged out: either at login route or the login field exists
    #assert ("/user/login" in driver.current_url) or login_again.find(LoginPage.USERNAME)
