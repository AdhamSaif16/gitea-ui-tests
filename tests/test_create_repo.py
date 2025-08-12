# tests/test_create_repo.py
import os
import sys
import uuid
import tempfile
import shutil
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

        # Unique Chrome profile per class (avoids "profile in use" on CI)
        cls.user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={cls.user_data_dir}")

        # Extra CI-friendly flags
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-gpu")

        cls.driver = webdriver.Chrome(options=options)

        # Config & creds (override via env)
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.username = os.getenv("GITEA_USERNAME", "uitester")
        cls.password = os.getenv("GITEA_PASSWORD", "TestPass123!")
        cls.api_token = os.getenv("GITEA_API_TOKEN")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            shutil.rmtree(cls.user_data_dir, ignore_errors=True)

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
        self.assertEqual(repo_page.get_repo_name(), repo_name)
        self.assertTrue(repo_page.get_repo_full_name().startswith(f"{self.username}/"))

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
