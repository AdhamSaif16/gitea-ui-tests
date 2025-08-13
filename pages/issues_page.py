# pages/issues_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class IssuesPage(BasePage):
    NEW_ISSUE_BUTTON = (By.CSS_SELECTOR, 'a.issue-list-new[href$="/issues/new"]')

    def wait_until_loaded(self, repo_full: str | None = None):
        # Prefer URL check if provided, but don't depend solely on it
        if repo_full:
            try:
                self.wait.until(EC.url_contains(f"/{repo_full}/issues"))
            except Exception:
                pass  # fall back to element-based readiness
        self.find(self.NEW_ISSUE_BUTTON)
        return self

    def click_new_issue(self, pause_seconds: float = 0):
        from .new_issue_page import NewIssuePage
        self.click(self.NEW_ISSUE_BUTTON)
        page = NewIssuePage(self.driver, self.base_url).wait_until_loaded()
        if pause_seconds:
            import time; time.sleep(pause_seconds)
        return page
