# -*- coding: utf-8 -*-
import os

import requests


def test_demo_pytest():
    base_url = os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"]

    requests.post(f"{base_url}/post")
    requests.get(f"{base_url}/get")
    requests.put(f"{base_url}/put")


def test_demo_raise_exception(fixture_which_do_not_exists):
    pass
