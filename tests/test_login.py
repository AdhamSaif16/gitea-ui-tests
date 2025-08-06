import os
import time
import tempfile
import unittest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load .env file
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

class GiteaLoginTest(unittest.TestCase):
    def setUp(self):
        options = Options()
        if HEADLESS:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        # Avoid Chrome profile conflicts
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

        if not HEADLESS:
            options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def tearDown(self):
        if not HEADLESS:
            time.sleep(5)
        self.driver.quit()

    def test_login_success(self):
        self.driver.get(f"{BASE_URL}/user/login")

        # Fill in login form
        self.driver.find_element(By.NAME, "user_name").send_keys(USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        # Wait for and click the Sign In button
        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ui.primary.button"))
        )
        # After clicking login button
        time.sleep(2)  # optional pause

        submit_btn.click()

        #print("🧭 Current URL:", self.driver.current_url)

        # Try either of these (only one is needed):
        WebDriverWait(self.driver, 10).until(
            EC.url_changes(f"{BASE_URL}/user/login")
        )



if __name__ == "__main__":
    unittest.main()
