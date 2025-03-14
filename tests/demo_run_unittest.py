import os
import unittest

import requests

BASE_URL = os.environ.get("HTTPDBG_TEST_UNITTEST_BASE_URL", "http://localhost:4909/")


def setUpModule():
    requests.get(f"{BASE_URL}/get?setup_module")


def tearDownModule():
    requests.get(f"{BASE_URL}/get?teardown_module")


class TestUnittests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        requests.get(f"{BASE_URL}/get?setup_class")

    @classmethod
    def tearDownClass(self):
        requests.get(f"{BASE_URL}/get?teardown_class")

    def setUp(self):
        requests.get(f"{BASE_URL}/get?setup")

    def tearDown(self):
        requests.get(f"{BASE_URL}/get?teardown")

    def test_case1(self):
        requests.get(f"{BASE_URL}/get?testcase1")

    def test_case2(self):
        requests.get(f"{BASE_URL}/get?testcase2")


if __name__ == "__main__":
    unittest.main()
