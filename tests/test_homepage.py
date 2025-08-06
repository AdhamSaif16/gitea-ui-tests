import os
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import time
import tempfile  
# Load environment variables from .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

class GiteaUITest(unittest.TestCase):


    def setUp(self):
        options = Options()

        if HEADLESS:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        #  Create unique temporary user data dir
        user_data_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={user_data_dir}")

        if not HEADLESS:
            options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)



    def tearDown(self):
        if not HEADLESS:
            print(" Waiting 5 seconds before closing the browser...")
            time.sleep(10)
        self.driver.quit()


    def test_homepage_title(self):
        self.driver.get(BASE_URL)
        self.assertIn("Gitea", self.driver.title)

if __name__ == "__main__":
    unittest.main()
