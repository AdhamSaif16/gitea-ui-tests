# pages/issue_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class IssuePage(BasePage):
    # Title shows as plain text near top; keep selectors flexible
    ISSUE_TITLE = (By.CSS_SELECTOR, 'h1, .issue-title, .content .header')

    def wait_until_loaded(self):
        # Issue pages include /issues/<number> in the URL
        self.wait.until(EC.url_matches(r".*/issues/\d+/?$"))
        self.find(self.ISSUE_TITLE)
        return self

    def get_title_text(self) -> str:
        return self.find(self.ISSUE_TITLE).text.strip()
