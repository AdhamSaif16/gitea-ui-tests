# pages/create_repo_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class CreateRepoPage(BasePage):
    REPO_NAME_INPUT   = (By.ID, "repo_name")
    DESCRIPTION_INPUT = (By.ID, "description")

    # CSS-only selectors (no XPath)
    # First try the submit inside the /repo/create form; fall back to the primary button on that page.
    CREATE_BUTTON_PRIMARY   = (By.CSS_SELECTOR, 'form[action="/repo/create"] button.ui.primary.button')
    CREATE_BUTTON_FALLBACK  = (By.CSS_SELECTOR, 'button.ui.primary.button')

    def wait_until_loaded(self):
        self.find(self.REPO_NAME_INPUT)
        return self

    def set_repo_name(self, name: str):
        self.type(self.REPO_NAME_INPUT, name)
        return self

    def set_description(self, desc: str):
        self.type(self.DESCRIPTION_INPUT, desc)
        return self

    def _wait_create_enabled(self):
        # Prefer the form-scoped button; if not found/clickable, fall back to any primary button.
        try:
            self.wait.until(EC.element_to_be_clickable(self.CREATE_BUTTON_PRIMARY))
            return self.driver.find_element(*self.CREATE_BUTTON_PRIMARY)
        except Exception:
            self.wait.until(EC.element_to_be_clickable(self.CREATE_BUTTON_FALLBACK))
            return self.driver.find_element(*self.CREATE_BUTTON_FALLBACK)

    def create_repository(self, pause_seconds: float = 0):
        btn = self._wait_create_enabled()
        try:
            btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", btn)

        if pause_seconds:
            import time; time.sleep(pause_seconds)

        from .repo_page import RepoPage
        page = RepoPage(self.driver, self.base_url)
        page.wait_until_loaded()
        return page
