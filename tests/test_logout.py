# tests/test_logout.py
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Make project root importable so "from pages..." works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from pages.login_page import LoginPage


class TestLogout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Unique Chrome profile per class (prevents "profile in use" on CI)
        cls.user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={cls.user_data_dir}")

        # Extra CI-friendly flags
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-gpu")

        cls.driver = webdriver.Chrome(options=options)

        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.username = os.getenv("GITEA_USERNAME", "uitester")
        cls.password = os.getenv("GITEA_PASSWORD", "TestPass123!")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            shutil.rmtree(cls.user_data_dir, ignore_errors=True)

    def test_logout_with_pom(self):
        login = LoginPage(self.driver, self.base_url).open()
        dashboard = login.login_as(self.username, self.password)

        login_again = dashboard.logout(pause_seconds=1.0)

        # Assert we’re logged out: redirected to homepage (BASE_URL)
        self.assertEqual(self.driver.current_url.rstrip("/"), self.base_url.rstrip("/"))


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
