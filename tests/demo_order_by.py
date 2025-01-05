import os
import time

import requests

BASE_URL = os.environ.get("HTTPDBG_TEST_ORDERBY_BASE_URL", "http://localhost:4909/")


def test_w1():
    time.sleep(1)
    requests.get(f"{BASE_URL}/w1_1")
    time.sleep(5)
    requests.get(f"{BASE_URL}/w1_5")


def test_w2():
    time.sleep(2)
    requests.get(f"{BASE_URL}/w2_2")
    time.sleep(5)
    requests.get(f"{BASE_URL}/w2_7")


def test_w3():
    time.sleep(10)
    requests.get(f"{BASE_URL}/w3_10")


def test_w4():
    requests.get(f"{BASE_URL}/w4_0")
    time.sleep(11)
