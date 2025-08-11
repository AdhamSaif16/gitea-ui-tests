# conftest.py
#This file gives pytest reusable fixtures:
#   -base_url reads your app URL from .env
#   -creds reads username/password from .env
#   -driver creates a Chrome WebDriver that works locally and in CI

import os, tempfile, pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load .env so BASE_URL, HEADLESS, USERNAME, PASSWORD are available
load_dotenv()

@pytest.fixture(scope="session")
def base_url():
    # normalize to avoid double slashes when we join paths
    return os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")

@pytest.fixture(scope="session")
def creds():
    # keep credentials out of code; store them in .env or GitHub secrets (for CI)
    return {
        "username": os.getenv("USERNAME", "uitester"),
        "password": os.getenv("PASSWORD", "TestPass123!"),
    }

@pytest.fixture
def driver():
    # allow headless switching via .env
    headless = os.getenv("HEADLESS", "false").lower() == "true"

    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")           # needed in many CI runners
        options.add_argument("--disable-dev-shm-usage")# avoids /dev/shm small size issues
    else:
        options.add_argument("--start-maximized")      # nicer when running locally

    # isolate Chrome profile to avoid “profile in use” errors in CI
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    # webdriver-manager auto-installs a compatible ChromeDriver
    drv = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield drv
    drv.quit()  # make sure Chrome closes even if a test fails
