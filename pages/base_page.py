# pages/base_page.py
#A base class with:

#   -open() to navigate by relative path
#   -find(), click(), type() with explicit waits
#   -url_contains() helper for navigation checks

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, timeout)

    def open(self, path: str):
        """Open a relative path like '/user/login'."""
        self.driver.get(f"{self.base_url}{path}")
        return self

    def find(self, locator):
        """Wait until element exists in the DOM, then return it."""
        return self.wait.until(EC.presence_of_element_located(locator))

    def click(self, locator):
        """Wait until element is clickable, then click it."""
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type(self, locator, text: str, clear=True):
        """Type text into an input, optionally clearing it first."""
        el = self.find(locator)
        if clear:
            el.clear()
        el.send_keys(text)

    def url_contains(self, fragment: str):
        """Wait until the URL contains a given fragment."""
        self.wait.until(EC.url_contains(fragment))
        return True
        # utility to try a list of locators until one is clickable.
    def click_first(self, locators):
        """Try clicking the first locator that becomes clickable."""
        last_err = None
        for loc in locators:
            try:
                self.wait.until(EC.element_to_be_clickable(loc)).click()
                return True
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err
        return False