# -*- coding: utf-8 -*-
import os

import pytest
import requests


def test_demo_pytest():
    base_url = os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"]

    requests.post(f"{base_url}/post")
    requests.get(f"{base_url}/get")
    requests.put(f"{base_url}/put")


def test_demo_raise_exception(fixture_which_does_not_exist):
    pass


@pytest.fixture
def my_fixture():
    base_url = os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"]

    requests.post(f"{base_url}/post")


def test_demo_pytest_fixture_tag(my_fixture):
    base_url = os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"]

    requests.get(f"{base_url}/get")
