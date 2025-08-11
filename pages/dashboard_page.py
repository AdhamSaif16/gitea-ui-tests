# pages/dashboard_page.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class DashboardPage(BasePage):

    # Toggle (use starts-with to avoid the Unicode ellipsis char)
    USER_MENU_TOGGLE = (By.CSS_SELECTOR, 'div.ui.dropdown.jump.item[aria-label^="Profile and Settings"]')
    # Logout inside the opened dropdown (uses data-url, not href)
    LOGOUT_LINK      = (By.CSS_SELECTOR, 'a.item.link-action[data-url="/user/logout"]')

    # Indicators that you are logged out
    SIGNIN_LINK = (By.CSS_SELECTOR, 'a[href="/user/login"], a[href="/user/signin"]')
    HOME_LOGO   = (By.CSS_SELECTOR, 'img.logo')
    NEW_REPO_BUTTON = (By.CSS_SELECTOR, "a[href='/repo/create']")
    NEW_REPO_LINK = (By.CSS_SELECTOR, 'a[href="/repo/create"][aria-label="New Repository"]')

    def wait_until_loaded(self):
        # Consider dashboard ready when the user menu toggle exists
        self.find(self.USER_MENU_TOGGLE)
        return self

    def open_user_menu(self, pause_seconds: float = 0):
        self.click(self.USER_MENU_TOGGLE)
        if pause_seconds:
            time.sleep(pause_seconds)  # visual pause to see dropdown open
        return self
    
    def go_to_new_repo(self, pause_seconds: float = 0):
        link = self.wait.until(EC.presence_of_element_located(self.NEW_REPO_LINK))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
        self.wait.until(EC.element_to_be_clickable(self.NEW_REPO_LINK)).click()
        if pause_seconds:
            import time; time.sleep(pause_seconds)
        from .create_repo_page import CreateRepoPage
        page = CreateRepoPage(self.driver, self.base_url)
        page.wait_until_loaded()
        return CreateRepoPage(self.driver, self.base_url)
    
    def logout(self, pause_seconds: float = 0):
        from .login_page import LoginPage  # avoid circular import

        # Try normal UI flow first
        try:
            self.open_user_menu(pause_seconds=pause_seconds)
            self.click(self.LOGOUT_LINK)
            if pause_seconds:
                time.sleep(pause_seconds)
        except Exception as e:
            print("[logout] Click flow failed, will try direct URL. Reason:", repr(e))
        
        #make sure we logged out
        self.wait.until(EC.presence_of_element_located(self.HOME_LOGO))
        time.sleep(3)
        return LoginPage(self.driver, self.base_url)

