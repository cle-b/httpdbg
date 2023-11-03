# -*- coding: utf-8 -*-
from httpdbg import httprecord

import pytest
import requests


@pytest.mark.cm
@pytest.mark.api
def test_context_manager(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1


@pytest.mark.cm
@pytest.mark.api
def test_context_manager_two_calls(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1
    for _, req in records.requests.items():
        assert req.method.lower() == "get"

    with httprecord() as records2:
        requests.post(httpbin.url + "/post")

    assert len(records2.requests) == 1
    for _, req in records2.requests.items():
        assert req.method.lower() == "post"


@pytest.mark.cm
def test_context_manager_reentrant(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records1:
        requests.get(httpbin.url + "/get/a1")
        with httprecord() as records2:
            requests.get(httpbin.url + "/get/b1")
            requests.get(httpbin.url + "/get/b2")
            with httprecord() as records3:
                requests.get(httpbin.url + "/get/c1")
        requests.get(httpbin.url + "/get/a2")

    requests.get(httpbin.url + "/get")

    assert len(records1.requests) == 5
    assert len(records2.requests) == 3
    assert len(records3.requests) == 1
