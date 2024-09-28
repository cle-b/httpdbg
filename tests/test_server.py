# -*- coding: utf-8 -*-
import requests

import pytest

from httpdbg.exception import HttpdbgException
from httpdbg.hooks.all import httprecord
from httpdbg.server import httpdbg_srv


@pytest.mark.server
@pytest.mark.parametrize("host", ["localhost", "0.0.0.0"])
def test_server_host(httpbin, host, httpdbg_port):
    with httpdbg_srv(host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get")

        ret = requests.get(f"http://localhost:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"


@pytest.mark.server
def test_server_host_exception_host(httpdbg_port):
    host = "1.2.3.4"
    with pytest.raises(HttpdbgException):
        with httpdbg_srv(host, httpdbg_port):
            pass


@pytest.mark.server
def test_server_host_exception_port():
    host = "127.0.0.1"
    port = 123456789
    with pytest.raises(HttpdbgException):
        with httpdbg_srv(host, port):
            pass
