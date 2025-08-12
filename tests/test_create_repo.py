# tests/test_create_repo.py
import os
import sys
import uuid
from pathlib import Path
import unittest
from urllib.parse import urlparse

# Make project root importable so "from pages..." works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from pages.login_page import LoginPage
from tests.utils.gitea_api import delete_repo


class TestCreateRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # WebDriver setup
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=options)

        # Config & creds (override via env)
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.username = os.getenv("GITEA_USERNAME", "uitester")
        cls.password = os.getenv("GITEA_PASSWORD", "TestPass123!")
        cls.api_token = os.getenv("GITEA_API_TOKEN")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_create_repository(self):
        # 1) Login
        login = LoginPage(self.driver, self.base_url).open()
        dashboard = login.login_as(self.username, self.password)

        # 2) Create repo
        repo_name = f"ui-test-repo-{uuid.uuid4().hex[:6]}"
        create_repo = dashboard.go_to_new_repo(pause_seconds=0.5)
        repo_page = (
            create_repo
            .set_repo_name(repo_name)
            .set_description("UI test repository")
            .create_repository(pause_seconds=0.5)
        )

        # 3) Assertions
        # By repo name only
        self.assertEqual(repo_page.get_repo_name(), repo_name)
        # Optional: also assert owner prefix
        self.assertTrue(repo_page.get_repo_full_name().startswith(f"{self.username}/"))

        # By URL (owner/repo at the end)
        path = urlparse(self.driver.current_url).path.rstrip("/")
        self.assertTrue(path.endswith(f"/{self.username}/{repo_name}"))

        # 4) Cleanup repo (if token available)
        if self.api_token:
            code = delete_repo(self.base_url, self.api_token, self.username, repo_name)
            print(f"[cleanup] DELETE /repos/{self.username}/{repo_name} -> {code}")
        else:
            print("[cleanup] GITEA_API_TOKEN not set, skipping repo deletion.")


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
