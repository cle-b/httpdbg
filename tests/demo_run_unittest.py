import os
import unittest

import requests

BASE_URL = os.environ.get("HTTPDBG_TEST_UNITTEST_BASE_URL", "http://localhost:4909/")

class TestUnittests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        requests.get(f"{BASE_URL}/setup_class")

    @classmethod
    def tearDownClass(self):
        requests.get(f"{BASE_URL}/teardown_class")

    def setUp(self):
        requests.get(f"{BASE_URL}/setup")

    def tearDown(self):
        requests.get(f"{BASE_URL}/teardown")

    def test_case1(self):
        requests.get(f"{BASE_URL}/testcase1")

    def test_case2(self):
        requests.get(f"{BASE_URL}/testcase2")


if __name__ == "__main__":
    unittest.main()
