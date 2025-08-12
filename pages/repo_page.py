# pages/repo_page.py
from selenium.webdriver.common.by import By
from .base_page import BasePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class RepoPage(BasePage):
    # <div role="main" aria-label="owner/repo[: description]" class="page-content repository ...">
    REPO_CONTAINER = (By.CSS_SELECTOR, 'div[role="main"][class*="repository"]')
    ISSUES_TAB = (By.CSS_SELECTOR, 'a.item[href$="/issues"]')
    REPO_NAV = (By.CSS_SELECTOR, 'div[role="main"][class*="repository"] .secondary.menu, nav, .repo-menu')

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

    def issues_link_locator(self):
        """Exact repo issues link: /owner/repo/issues"""
        full = self.get_repo_full_name()
        return (By.CSS_SELECTOR, f'a.item[href="/{full}/issues"]')
    
    def get_repo_name(self) -> str:
        """e.g., 'ui-test-repo-8a91a4'"""
        core = self._aria_label_core()
        return core.split("/", 1)[-1] if "/" in core else core

    def go_to_issues(self, pause_seconds: float = 0):
        from .issues_page import IssuesPage

        full = self.get_repo_full_name()  # "owner/repo"
        locator = (By.CSS_SELECTOR, f'a.item[href="/{full}/issues"]')

        # Try clicking within the repo’s own nav area first
        try:
            nav = self.find(self.REPO_NAV)
            nav.find_element(*locator).click()
        except Exception:
            # Fallback: direct URL
            self.driver.get(f"{self.base_url}/{full}/issues")

        # After click, give it a short window to land correctly
        try:
            WebDriverWait(self.driver, 5).until(
                EC.any_of(
                    EC.url_contains(f"/{full}/issues"),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.issue-list-new[href$="/issues/new"]'))
                )
            )
        except Exception:
            # Final fallback: navigate directly
            self.driver.get(f"{self.base_url}/{full}/issues")

        page = IssuesPage(self.driver, self.base_url)
        page.wait_until_loaded(repo_full=full)
        if pause_seconds:
            import time; time.sleep(pause_seconds)
        return page
