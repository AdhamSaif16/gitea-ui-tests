# pages/repo_page.py
from selenium.webdriver.common.by import By
from .base_page import BasePage

class RepoPage(BasePage):
    # <div role="main" aria-label="owner/repo[: description]" class="page-content repository ...">
    REPO_CONTAINER = (By.CSS_SELECTOR, 'div[role="main"][class*="repository"]')

    def wait_until_loaded(self):
        self.find(self.REPO_CONTAINER)
        return self

    def _aria_label_core(self) -> str:
        """Return the aria-label without any trailing ': description'."""
        el = self.find(self.REPO_CONTAINER)
        raw = el.get_attribute("aria-label") or ""
        return raw.split(":", 1)[0].strip()  # keep only 'owner/repo'

    def get_repo_full_name(self) -> str:
        """e.g., 'uitester/ui-test-repo-8a91a4'"""
        return self._aria_label_core()

    def get_repo_name(self) -> str:
        """e.g., 'ui-test-repo-8a91a4'"""
        core = self._aria_label_core()
        return core.split("/", 1)[-1] if "/" in core else core
