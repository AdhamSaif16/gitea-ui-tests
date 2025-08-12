# tests/test_create_issue.py
import os
import sys
import uuid
import unittest
import tempfile
import shutil
from pathlib import Path

# Make project root importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from selenium import webdriver
from pages.login_page import LoginPage
from tests.utils.gitea_api import delete_repo


class TestCreateIssue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Chrome options
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # unique Chrome profile per class (prevents "profile in use" on CI)
        cls.user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={cls.user_data_dir}")

        # Extra CI-friendly flags
        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-gpu")

        cls.driver = webdriver.Chrome(options=options)

        # Config/creds
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.creds = {
            "username": os.getenv("GITEA_USERNAME", "uitester"),
            "password": os.getenv("GITEA_PASSWORD", "TestPass123!"),
        }

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            shutil.rmtree(cls.user_data_dir, ignore_errors=True)

    def setUp(self):
        # keep a list of (owner, repo_name) to delete even if the test fails
        self._repos_to_cleanup: list[tuple[str, str]] = []

    def tearDown(self):
        api_token = os.getenv("GITEA_API_TOKEN")
        if not self._repos_to_cleanup:
            return

        if not api_token:
            print("[teardown] GITEA_API_TOKEN not set, skipping repo deletion for:",
                  self._repos_to_cleanup)
            return

        for owner, repo_name in self._repos_to_cleanup:
            try:
                code = delete_repo(self.base_url, api_token, owner, repo_name)
                print(f"[teardown] DELETE /repos/{owner}/{repo_name} -> {code}")
            except Exception as e:
                print(f"[teardown] failed to delete {owner}/{repo_name}: {e}")

    def test_create_issue(self):
        # 1) Login
        login = LoginPage(self.driver, self.base_url).open()
        dashboard = login.login_as(self.creds["username"], self.creds["password"])

        # 2) Create a repo for the issue
        repo_name = f"ui-issue-repo-{uuid.uuid4().hex[:6]}"
        repo_page = (
            dashboard.go_to_new_repo()
            .set_repo_name(repo_name)
            .set_description("Temp repo for issue test")
            .create_repository()
        )

        # mark for cleanup ASAP so we delete even if later assertions fail
        self._repos_to_cleanup.append((self.creds["username"], repo_name))

        # 3) New Issue
        new_issue = repo_page.go_to_issues().click_new_issue()

        # 4) Create the issue
        title = f"Issue title {uuid.uuid4().hex[:4]}"
        body = "This is a UI test issue body."
        issue_page = new_issue.set_title(title).set_body(body).submit()

        # 5) Verify
        self.assertTrue(issue_page.get_title_text().startswith(title))


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
