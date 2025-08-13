# pages/new_issue_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class NewIssuePage(BasePage):
    TITLE_INPUT   = (By.CSS_SELECTOR, "#issue_title, input#issue_title, input[name='title']")
    BODY_TEXTAREA = (By.CSS_SELECTOR, "#issue_content, textarea#issue_content, textarea[name='content']")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button.ui.primary.button")

    def wait_until_loaded(self):
        self.find(self.TITLE_INPUT)
        return self

    def set_title(self, title: str):
        self.type(self.TITLE_INPUT, title)
        return self

    def set_body(self, body: str):
        try:
            self.type(self.BODY_TEXTAREA, body)
        except Exception:
            pass
        return self

    def submit(self, pause_seconds: float = 3):
        from .issue_page import IssuePage

        # wait until the button is clickable, then click (with JS fallback)
        self.wait.until(EC.element_to_be_clickable(self.SUBMIT_BUTTON))
        btn = self.driver.find_element(*self.SUBMIT_BUTTON)
        try:
            btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", btn)

        page = IssuePage(self.driver, self.base_url).wait_until_loaded()
        if pause_seconds:
            import time; time.sleep(pause_seconds)
        return page
