import unittest
import requests


class TestUnittests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        requests.get("http://localhost:4909/setup_class")

    @classmethod
    def tearDownClass(self):
        requests.get("http://localhost:4909/teardown_class")

    def setUp(self):
        requests.get("http://localhost:4909/setup")

    def tearDown(self):
        requests.get("http://localhost:4909/teardown")

    def test_case1(self):
        requests.get("http://example.com")

    def test_case2(self):
        requests.get("http://example.com")


if __name__ == "__main__":
    unittest.main()
