# -*- coding: utf-8 -*-
from httpdbg import httpdbg

import pytest
import requests


@pytest.mark.cm
@pytest.mark.api
def test_context_manager(httpbin):

    requests.get(httpbin.url + "/get")

    with httpdbg() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1


@pytest.mark.cm
@pytest.mark.api
def test_context_manager_two_calls(httpbin):

    requests.get(httpbin.url + "/get")

    with httpdbg() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1
    for _, req in records.requests.items():
        assert req.method.lower() == "get"

    with httpdbg() as records2:
        requests.post(httpbin.url + "/post")

    assert len(records2.requests) == 1
    for _, req in records2.requests.items():
        assert req.method.lower() == "post"


@pytest.mark.cm
def test_context_manager_reentrant(httpbin):

    requests.get(httpbin.url + "/get")

    with httpdbg() as records:
        with httpdbg() as records2:
            requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1
    assert len(records2.requests) == 1
