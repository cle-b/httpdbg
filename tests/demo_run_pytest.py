# -*- coding: utf-8 -*-
import os

import requests


def test_demo():
    base_url = os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"]

    requests.post(f"{base_url}/post")
    requests.get(f"{base_url}/get")
    requests.put(f"{base_url}/put")
