# tests/test_create_repo.py
import uuid
from urllib.parse import urlparse
from pages.login_page import LoginPage

def test_create_repository(driver, base_url, creds):
    login = LoginPage(driver, base_url).open()
    dashboard = login.login_as(creds["username"], creds["password"])

    repo_name = f"ui-test-repo-{uuid.uuid4().hex[:6]}"

    create_repo = dashboard.go_to_new_repo(pause_seconds=0.5)
    repo_page = (
        create_repo
        .set_repo_name(repo_name)
        .set_description("UI test repository")
        .create_repository(pause_seconds=0.5)
    )

    
    # Assert by repo name only
    assert repo_page.get_repo_name() == repo_name
    # (optional) also assert owner:
    assert repo_page.get_repo_full_name().startswith(f"{creds['username']}/")


    # Assert by URL (owner/repo)
    path = urlparse(driver.current_url).path.rstrip("/")
    assert path.endswith(f"/{creds['username']}/{repo_name}")
