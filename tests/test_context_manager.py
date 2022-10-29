# -*- coding: utf-8 -*-
import requests

import pytest

from httpdbg import httpdbg
from httpdbg.webapp import httpdebugk7


@pytest.mark.cm
def test_context_manager(httpbin, httpdbg_port):

    requests.get(httpbin.url + "/get")

    with httpdbg(httpdbg_port):
        requests.get(httpbin.url + "/get")

    assert len(httpdebugk7.requests) == 1


@pytest.mark.cm
def test_context_manager_reentrant(httpbin, httpdbg_port):

    requests.get(httpbin.url + "/get")

    with httpdbg(httpdbg_port):
        with httpdbg(httpdbg_port + 1000):
            requests.get(httpbin.url + "/get")

    assert len(httpdebugk7.requests) == 1


@pytest.mark.cm
def test_context_manager_two_calls(httpbin, httpdbg_port):

    requests.get(httpbin.url + "/get")

    with httpdbg(httpdbg_port):
        requests.get(httpbin.url + "/get")

    assert len(httpdebugk7.requests) == 1
    for _, req in httpdebugk7.requests.items():
        assert req.request.method.lower() == "get"

    with httpdbg(httpdbg_port + 1000):
        requests.post(httpbin.url + "/post")

    assert len(httpdebugk7.requests) == 1
    for _, req in httpdebugk7.requests.items():
        assert req.request.method.lower() == "post"
