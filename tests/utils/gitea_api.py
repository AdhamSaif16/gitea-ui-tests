# tests/utils/gitea_api.py
import requests

def delete_repo(base_url: str, token: str, owner: str, repo: str) -> int:
    """
    Deletes a repository via Gitea API.
    Returns HTTP status (204 on success).
    """
    url = f"{base_url.rstrip('/')}/api/v1/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}"}
    resp = requests.delete(url, headers=headers, timeout=20)
    return resp.status_code
