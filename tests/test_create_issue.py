# tests/test_create_issue.py
import os
import uuid
import unittest
from selenium import webdriver
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # one level up from tests/
sys.path.insert(0, str(ROOT))

from pages.login_page import LoginPage
from pages.login_page import LoginPage
from tests.utils.gitea_api import delete_repo

class TestCreateIssue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure WebDriver
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=options)

        # Config/creds
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        cls.creds = {
            "username": os.getenv("GITEA_USERNAME", "uitester"),
            "password": os.getenv("GITEA_PASSWORD", "TestPass123!"),
        }

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_create_issue(self):
        API_TOKEN = os.getenv("GITEA_API_TOKEN")

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

        # 3) New Issue
        new_issue = repo_page.go_to_issues().click_new_issue()

        # 4) Create the issue
        title = f"Issue title {uuid.uuid4().hex[:4]}"
        body = "This is a UI test issue body."
        issue_page = new_issue.set_title(title).set_body(body).submit()

        # 5) Verify
        self.assertTrue(issue_page.get_title_text().startswith(title))

        # 6) Cleanup repo
        if API_TOKEN:
            code = delete_repo(self.base_url, API_TOKEN, self.creds["username"], repo_name)
            print(f"[cleanup] DELETE /repos/{self.creds['username']}/{repo_name} -> {code}")
        else:
            print("[cleanup] GITEA_API_TOKEN not set, skipping repo deletion.")

if __name__ == "__main__":
    # Avoid SystemExit stopping VS Code debugger
    unittest.main(verbosity=2, exit=False)
