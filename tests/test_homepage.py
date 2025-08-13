# tests/test_homepage_title.py
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Make project root importable so "from pages..." (if needed later) works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver


class TestHomepageTitle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Headless by default unless HEADLESS="0"
        headless_env = os.getenv("HEADLESS", "1")
        cls.headless = headless_env not in ("0", "false", "False")

        options = webdriver.ChromeOptions()
        if cls.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Unique Chrome profile per class
        cls.user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={cls.user_data_dir}")

        # Extra CI-friendly flags
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-gpu")

        cls.driver = webdriver.Chrome(options=options)

        # Base URL with sensible default
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            shutil.rmtree(cls.user_data_dir, ignore_errors=True)

    def test_homepage_title(self):
        self.driver.get(self.base_url)
        self.assertIn("Gitea", self.driver.title)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
