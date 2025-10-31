import unittest
import time
import os
import threading
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestLocalLogin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        env_url = os.environ.get("QA_BASE_URL")
        if env_url:
            cls.base_url = env_url
            cls._local_server = None
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            handler = partial(SimpleHTTPRequestHandler, directory=project_root)

            server = HTTPServer(("127.0.0.1", 0), handler)
            host, port = server.server_address
            cls._local_server = server
            cls._server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            cls._server_thread.start()
            timeout = 5.0
            start = time.time()
            while True:
                try:
                    with socket.create_connection((host, port), timeout=0.5):
                        break
                except OSError:
                    if time.time() - start > timeout:
                        raise RuntimeError("Failed to start local HTTP server for tests")
                    time.sleep(0.05)
            cls.base_url = f"http://{host}:{port}/web_app/login.html"
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(5)

    def test_valid_login(self):
        d = self.driver
        d.get(self.base_url)
        d.find_element(By.ID, "username").clear()
        d.find_element(By.ID, "username").send_keys("student")
        d.find_element(By.ID, "password").send_keys("Password123")
        d.find_element(By.ID, "loginBtn").click()
        time.sleep(1)
        body_text = d.find_element(By.TAG_NAME, "body").text
        self.assertIn("Dashboard", body_text, "Expected Dashboard after successful login")

    def test_invalid_password(self):
        d = self.driver
        d.get(self.base_url)
        d.find_element(By.ID, "username").clear()
        d.find_element(By.ID, "username").send_keys("student")
        d.find_element(By.ID, "password").send_keys("wrongpass")
        d.find_element(By.ID, "loginBtn").click()
        time.sleep(0.5)
        msg = d.find_element(By.ID, "message").text
        self.assertEqual(msg, "Invalid credentials", "Expected invalid credentials message")

    def test_empty_fields(self):
        d = self.driver
        d.get(self.base_url)
        d.find_element(By.ID, "username").clear()
        d.find_element(By.ID, "password").clear()
        d.find_element(By.ID, "loginBtn").click()
        time.sleep(0.5)
        msg = d.find_element(By.ID, "message").text
        self.assertEqual(msg, "Username & Password are required", "Expected required fields message")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass
        if getattr(cls, "_local_server", None):
            try:
                cls._local_server.shutdown()
                cls._local_server.server_close()
            except Exception:
                pass
            if getattr(cls, "_server_thread", None):
                cls._server_thread.join(timeout=1)

if __name__ == "__main__":
    unittest.main()
