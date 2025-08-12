# tests/test_login.py
import os
import sys
import time
import unittest
from pathlib import Path

# Make project root importable so "from pages..." works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from pages.login_page import LoginPage


class TestLogin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # WebDriver setup
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=options)

        # Config & creds
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.username = os.getenv("GITEA_USERNAME", "uitester")
        cls.password = os.getenv("GITEA_PASSWORD", "TestPass123!")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_login_with_pom(self):
        login = LoginPage(self.driver, self.base_url).open()
        dashboard = login.login_as(self.username, self.password)
        self.assertNotIn("/user/login", self.driver.current_url)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
