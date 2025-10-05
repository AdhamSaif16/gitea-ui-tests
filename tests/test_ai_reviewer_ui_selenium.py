# tests/test_ai_reviewer_ui_selenium.py
import os
import sys
import uuid
import time
import base64
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from urllib.parse import urlparse

# Ensure project root for POM imports like "from pages..."
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.login_page import LoginPage

PAUSE = 2.0  # pause ~2s after each "main" step


class TestAIReviewerUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ---- WebDriver (CI friendly) ----
        options = webdriver.ChromeOptions()
        if os.getenv("HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Unique Chrome profile per class (avoids "profile in use" on CI)
        cls.user_data_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        options.add_argument(f"--user-data-dir={cls.user_data_dir}")

        options.add_argument("--remote-debugging-port=0")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-gpu")

        cls.driver = webdriver.Chrome(options=options)

        # ---- Config ----
        cls.base_url = os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")
        cls.username = os.getenv("GITEA_USERNAME", "uitester")
        cls.password = os.getenv("GITEA_PASSWORD", "TestPass123!")
        cls.api_token = os.getenv("GITEA_API_TOKEN")  # required for API ops

        # Target existing repo (defaults)
        cls.target_owner = os.getenv("AI_REPO_OWNER", cls.username)
        cls.target_repo = os.getenv("AI_REPO_NAME", "ai-review-demo")

        # AI detection knobs (relaxed; can override via env)
        cls.expected_label_contains = os.getenv("AI_REVIEW_LABEL_CONTAINS", "risk").lower()
        cls.expected_comment_hint = os.getenv("AI_REVIEW_COMMENT_HINT", "risk").lower()
        cls.ai_reviewer_login_hint = os.getenv("AI_REVIEW_BOT_HINT", "ai").lower()

        # API client
        cls.api = requests.Session()
        if cls.api_token:
            cls.api.headers.update({"Authorization": f"token {cls.api_token}"})
        cls.api.headers.update({"Content-Type": "application/json"})
        cls.api_base = f"{cls.base_url}/api/v1"

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        finally:
            shutil.rmtree(cls.user_data_dir, ignore_errors=True)

    # ---------------- Core API helpers ----------------
    def _api_get(self, path, **params):
        r = self.api.get(f"{self.api_base}{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def _api_post(self, path, payload):
        r = self.api.post(f"{self.api_base}{path}", data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        return r.json()

    def _api_patch(self, path, payload):
        r = self.api.patch(f"{self.api_base}{path}", data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        return r.json()

    # ------------ Repo/branch helpers ------------
    def _get_repo(self, owner, repo):
        return self._api_get(f"/repos/{owner}/{repo}")

    def _get_default_branch(self, owner, repo):
        data = self._get_repo(owner, repo)
        return data.get("default_branch") or "main"

    def _wait_for_branch_exists(self, owner, repo, branch, timeout_sec=60, poll=1.0):
        deadline = time.time() + timeout_sec
        last_err = None
        while time.time() < deadline:
            try:
                data = self._api_get(f"/repos/{owner}/{repo}/branches/{branch}")
                commit = (data or {}).get("commit") or {}
                sha = commit.get("id") or commit.get("sha")
                if sha:
                    return sha
            except requests.HTTPError as e:
                last_err = e
            time.sleep(poll)
        raise RuntimeError(f"Branch {branch} not found within {timeout_sec}s (last_err={last_err})")

    def _create_file_on_new_branch(self, owner, repo, from_branch, new_branch, path, content_str, message):
        """
        Create a new branch from `from_branch` and write `path` in a single Contents API call.
        POST /repos/{owner}/{repo}/contents/{path}
        body: { branch: from_branch, new_branch: new_branch, message, content }
        """
        b64 = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
        payload = {
            "message": message,
            "content": b64,
            "branch": from_branch,
            "new_branch": new_branch,
        }
        return self._api_post(f"/repos/{owner}/{repo}/contents/{path}", payload)

    # ------------ PR helpers ------------
    def _open_pr(self, owner, repo, head_branch, base_branch, title, body=""):
        # Use explicit owner:branch form for head
        return self._api_post(
            f"/repos/{owner}/{repo}/pulls",
            {"head": f"{owner}:{head_branch}", "base": base_branch, "title": title, "body": body},
        )

    def _get_pr(self, owner, repo, index):
        return self._api_get(f"/repos/{owner}/{repo}/pulls/{index}")

    def _close_pr(self, owner, repo, index):
        try:
            return self._api_patch(f"/repos/{owner}/{repo}/pulls/{index}", {"state": "closed"})
        except requests.HTTPError:
            return self._api_patch(f"/repos/{owner}/{repo}/issues/{index}", {"state": "closed"})

    def _list_pr_labels(self, owner, repo, index):
        pr = self._get_pr(owner, repo, index)
        return pr.get("labels", [])

    def _list_issue_comments(self, owner, repo, index):
        return self._api_get(f"/repos/{owner}/{repo}/issues/{index}/comments")

    def _list_pr_review_comments(self, owner, repo, index):
        try:
            return self._api_get(f"/repos/{owner}/{repo}/pulls/{index}/comments")
        except Exception:
            return []

    def _list_pr_reviews(self, owner, repo, index):
        try:
            return self._api_get(f"/repos/{owner}/{repo}/pulls/{index}/reviews")
        except Exception:
            return []

    def _resolve_pr_index(self, pr_resp, owner, repo, head_branch, title_hint=None):
        for k in ("index", "number", "id"):
            v = pr_resp.get(k)
            if isinstance(v, int):
                return v
        for k in ("html_url", "url"):
            url = pr_resp.get(k)
            if url:
                try:
                    tail = url.rstrip("/").split("/")[-1]
                    return int(tail)
                except Exception:
                    pass
        pulls = self._api_get(f"/repos/{owner}/{repo}/pulls", state="open")
        for p in pulls:
            head = (p.get("head") or {})
            if head.get("ref") == head_branch:
                return p.get("index") or p.get("number") or p.get("id")
        if title_hint:
            for p in pulls:
                if p.get("title") == title_hint:
                    return p.get("index") or p.get("number") or p.get("id")
        raise RuntimeError(f"Could not resolve PR index. Create response: {pr_resp}")

    # ------------ UI nav helpers (use your provided selectors) ------------
    def _click_pull_requests_tab(self, drv):
        """
        Clicks the 'Pull Requests' tab using:
          span.resize-for-semibold[data-text='Pull Requests']  -> ancestor <a>
        Falls back to direct nav if needed.
        """
        try:
            # Wait for the tab label <span>
            el = WebDriverWait(drv, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span.resize-for-semibold[data-text='Pull Requests']")
                )
            )
            # Click its ancestor <a>
            link = el.find_element(By.XPATH, "./ancestor::a[1]")
            drv.execute_script("arguments[0].click();", link)
        except Exception:
            # Fallback: go directly
            # Try to infer owner/repo from current URL (/owner/repo[/...])
            try:
                parts = urlparse(drv.current_url).path.strip("/").split("/")
                owner, repo = parts[0], parts[1]
                drv.get(f"{self.base_url}/{owner}/{repo}/pulls")
            except Exception:
                raise
        # Wait a beat for list to render
        WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(PAUSE)

    def _open_pr_in_list(self, drv, owner, repo, pr_index=None, title_hint=None):
        """
        On the Pull Requests list page, click the PR row:
          primary selector: a.tw-no-underline.issue-title  (your screenshot)
          fallback: a[href$='/pulls/{index}']
        """
        # Ensure we are on the pulls list
        if "/pulls" not in urlparse(drv.current_url).path:
            drv.get(f"{self.base_url}/{owner}/{repo}/pulls")
            WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Prefer matching by title text
        if title_hint:
            try:
                link = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//a[contains(@class,'tw-no-underline') and contains(@class,'issue-title') and normalize-space()='{title_hint}']")
                    )
                )
                drv.execute_script("arguments[0].click();", link)
                WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(PAUSE)
                return
            except Exception:
                pass

        # Fallback: use PR index in href
        if pr_index is not None:
            try:
                link = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"a.tw-no-underline.issue-title[href$='/pulls/{pr_index}']")
                    )
                )
                drv.execute_script("arguments[0].click();", link)
                WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(PAUSE)
                return
            except Exception:
                # broader fallback: any anchor to /pulls/{index}
                try:
                    link = WebDriverWait(drv, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, f"a[href$='/pulls/{pr_index}']")
                        )
                    )
                    drv.execute_script("arguments[0].click();", link)
                    WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(PAUSE)
                    return
                except Exception:
                    pass

        raise RuntimeError("Could not open the newly created PR from the list page.")

    # ------------ AI wait (with periodic UI refresh) ------------
    def _wait_for_ai_review_with_ui_refresh(
        self, owner, repo, index, drv, pr_html_url, timeout_sec=360, poll=5, refresh_every=10
    ):
        deadline = time.time() + timeout_sec
        next_refresh = time.time()

        def comment_hits(cbody, clogin):
            t = (cbody or "").lower()
            u = (clogin or "").lower()
            return (
                (self.expected_comment_hint and self.expected_comment_hint in t) or
                "security" in t or "secret" in t or "eval" in t or "risk" in t or
                (self.ai_reviewer_login_hint and self.ai_reviewer_login_hint in u) or
                "bot" in u or "reviewer" in u
            )

        while time.time() < deadline:
            try:
                labels = self._list_pr_labels(owner, repo, index)
                has_label = any(
                    self.expected_label_contains in (lbl.get("name", "").lower()) or
                    "security" in (lbl.get("name", "").lower()) or
                    "risk" in (lbl.get("name", "").lower())
                    for lbl in labels
                )

                issue_comments = self._list_issue_comments(owner, repo, index)
                review_comments = self._list_pr_review_comments(owner, repo, index)
                reviews = self._list_pr_reviews(owner, repo, index)

                has_comment = False
                for c in issue_comments:
                    if comment_hits(c.get("body"), ((c.get("user") or {}).get("login"))):
                        has_comment = True
                        break
                if not has_comment:
                    for c in review_comments:
                        if comment_hits(c.get("body"), ((c.get("user") or {}).get("login"))):
                            has_comment = True
                            break
                if not has_comment:
                    for r in reviews:
                        if comment_hits(r.get("body"), ((r.get("user") or {}).get("login"))):
                            has_comment = True
                            break

                if has_label and has_comment:
                    return True

            except Exception as e:
                print("[wait] transient error:", e)

            # Periodic UI refresh to show new comments/labels
            now = time.time()
            if now >= next_refresh:
                try:
                    if not drv.current_url.startswith(pr_html_url):
                        drv.get(pr_html_url)
                    else:
                        drv.refresh()
                    WebDriverWait(drv, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
                except Exception:
                    pass
                next_refresh = now + refresh_every

            time.sleep(poll)

        return False

    # ---------------- The test ----------------
    def test_ai_reviewer_comment_and_label_visible(self):
        if not self.api_token:
            self.skipTest("GITEA_API_TOKEN is required for this test.")

        drv = self.driver

        # 1) Login (UI)
        login = LoginPage(drv, self.base_url).open()
        dashboard = login.login_as(self.username, self.password)
        self.assertNotIn("/user/login", drv.current_url)
        time.sleep(PAUSE)

        owner = self.target_owner
        repo = self.target_repo

        # 2) Navigate to existing repo page (UI)
        repo_html_url = f"{self.base_url}/{owner}/{repo}"
        drv.get(repo_html_url)
        try:
            WebDriverWait(drv, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:
            pass
        time.sleep(PAUSE)

        # 3) Prepare PR via API on existing repo
        default_branch = self._get_default_branch(owner, repo)
        _ = self._wait_for_branch_exists(owner, repo, default_branch, timeout_sec=60, poll=1.0)
        time.sleep(PAUSE)

        feature_branch = f"feat-ai-{uuid.uuid4().hex[:6]}"

        # Create the feature branch **and** write the insecure file in a single call
        insecure_py = """\
# Demo file intentionally insecure for automated review tests.
import os

# WARNING: insecure pattern for testing
def run_user_code():
    # eval is dangerous
    user_in = input("code> ")
    return eval(user_in)

AWS_ACCESS_KEY_ID = "AKIA" + "FAKEFAKEFAKEFAKE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY"  # fake, for testing

# TODO(security): sanitize inputs properly
if __name__ == "__main__":
    print("Insecure demo loaded")
"""
        self._create_file_on_new_branch(
            owner,
            repo,
            from_branch=default_branch,
            new_branch=feature_branch,
            path="insecure_demo.py",
            content_str=insecure_py,
            message="chore: add insecure demo that should trigger AI review",
        )
        time.sleep(PAUSE)

        # 4) Open PR
        pr_title = "AI-review demo: add insecure sample to trigger reviewer"
        pr_body = (
            "This PR intentionally adds an insecure pattern (eval), fake secrets, and a security TODO "
            "to trigger the AI review."
        )
        pr = self._open_pr(owner, repo, feature_branch, default_branch, pr_title, pr_body)
        time.sleep(PAUSE)

        # Resolve PR index
        pr_index = self._resolve_pr_index(pr, owner, repo, feature_branch, title_hint=pr_title)

        # 5) UI: Click Pull Requests tab, then click the new PR entry
        self._click_pull_requests_tab(drv)
        self._open_pr_in_list(drv, owner, repo, pr_index=pr_index, title_hint=pr_title)
        time.sleep(PAUSE)

        # Derive PR page URL (for refresher)
        pr_html_url = f"{self.base_url}/{owner}/{repo}/pulls/{pr_index}"

        # 6) Wait for AI review (label + comment), refreshing the UI periodically
        ai_timeout = int(os.getenv("AI_WAIT_SECS", "360"))
        ok = self._wait_for_ai_review_with_ui_refresh(
            owner, repo, pr_index, drv, pr_html_url, timeout_sec=ai_timeout, poll=5, refresh_every=10
        )
        self.assertTrue(ok, "AI review did not add expected label/comment within timeout")

        # --- refresh to see the AI comment ---
        try:
            # Hard reload of the PR page (safer than refresh when sessions redirect)
            pr_html_url = f"{self.base_url}/{owner}/{repo}/pulls/{pr_index}"
            self.driver.get(pr_html_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )

            # Optionally wait until a comment containing the hint is visible
            hint = self.expected_comment_hint or "risk"
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(@class,'comment') or contains(@class,'timeline')]" 
                    f"[.//*/text()[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{hint}')]]"
                ))
            )
        except Exception:
            # Fallback: soft refresh a couple of times
            for _ in range(2):
                try:
                    self.driver.refresh()
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                    )
                    time.sleep(2)
                except Exception:
                    time.sleep(1)

        time.sleep(5)  # small settle pause before cleanup
        #added comment

        # 7) Close the PR (API)
        self._close_pr(owner, repo, pr_index)
        time.sleep(PAUSE)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
