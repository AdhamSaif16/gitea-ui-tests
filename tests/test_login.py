# tests/test_login.py
from pages.login_page import LoginPage
import time

def test_login_with_pom(driver, base_url, creds):
    login = LoginPage(driver, base_url).open()
    dashboard = login.login_as(creds["username"], creds["password"])
    time.sleep(3)
    # simple assertion in the test (not inside page objects)
    assert "/user/login" not in driver.current_url
