# pages/login_page.py
#Encapsulates:
#   -Locators (username, password, sign-in)
#   -Actions (open(), login_as(...))
#   -Returns a DashboardPage to enable page chaining

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .base_page import BasePage
from .dashboard_page import DashboardPage

class LoginPage(BasePage):
    # Locators are tuples (By, value); store them centrally to change once if UI changes
    USERNAME = (By.NAME, "user_name")
    PASSWORD = (By.NAME, "password")
    SUBMIT   = (By.CSS_SELECTOR, "button.ui.primary.button")  # matches your “Sign In” button

    def open(self):
        """Navigate to the login page and verify it loaded (by waiting for username field)."""
        super().open("/user/login")
        self.find(self.USERNAME)  # lightweight “page loaded” check
        return self


    def login_as(self, username: str, password: str):
        """Perform login and return DashboardPage (page chaining)."""
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)

        # Capture the login URL to detect navigation
        old_url = self.driver.current_url
        self.click(self.SUBMIT)

        # Wait until we leave the login page (works whether we go to / or /dashboard)
        WebDriverWait(self.driver, 15).until(EC.url_changes(old_url))

        dash = DashboardPage(self.driver, self.base_url)
        dash.wait_until_loaded()
        return dash

