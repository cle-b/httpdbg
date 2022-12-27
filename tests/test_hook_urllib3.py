# -*- coding: utf-8 -*-
import sys
from unittest.mock import patch

import pytest
import urllib3

from httpdbg.server import httpdbg


@pytest.mark.urllib3
def test_urllib3(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request("GET", f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False


@pytest.mark.urllib3
def test_urllib3_initiator(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request("GET", f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == "test_urllib3_initiator"
    assert (
        http_record.initiator.long_label
        == "tests/test_hook_urllib3.py::test_urllib3_initiator"
    )
    assert 'http.request("GET", f"{httpbin.url}/get")' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.urllib3
def test_urllib3_request(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request(
            "POST", f"{httpbin.url}/post", body="abc", headers={"Content-Length": "3"}
        )

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == "abc"


@pytest.mark.urllib3
def test_urllib3_response(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request(
            "PUT",
            f"{httpbin.url}/put?azerty",
            body="def",
            headers={"Content-Length": "3"},
        )

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert {
        "name": "Content-Type",
        "value": "application/json",
    } in http_record.response.headers
    assert http_record.response.cookies == []
    assert b'"args":{"azerty":""}' in http_record.response.content
    assert b'"data":"def"' in http_record.response.content


@pytest.mark.urllib3
def test_urllib3_cookies(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request(
            "GET",
            f"{httpbin.url}/cookies/set/confiture/oignon",
            headers={"Content-Length": "3", "Cookie": "jam=strawberry"},
            redirect=False,
        )

    assert len(records) == 1

    http_record = records[0]
    assert {
        "name": "jam",
        "value": "strawberry",
    } in http_record.request.cookies

    assert {
        "attributes": [{"attr": "/", "name": "path"}],
        "name": "confiture",
        "value": "oignon",
    } in http_record.response.cookies


@pytest.mark.urllib3
def test_urllib3_redirect(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request("GET", f"{httpbin.url}/redirect-to?url={httpbin.url}/get")

    assert len(records) == 2
    assert records[0].url == f"{httpbin.url}/redirect-to?url={httpbin.url}/get"
    assert records[1].url == f"{httpbin.url}/get"


@pytest.mark.urllib3
def test_urllib3_not_found(httpbin):
    with httpdbg() as records:
        http = urllib3.PoolManager()
        http.request("GET", f"{httpbin.url}/404")

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.urllib3
def test_urllib3_exception():
    with httpdbg() as records:
        with pytest.raises(urllib3.exceptions.MaxRetryError):
            http = urllib3.PoolManager()
            http.request("GET", "http://f.q.d.1234.n.t.n.e/")

    http_record = records[-1]

    assert http_record.url == "http://f.q.d.1234.n.t.n.e/"
    assert http_record.method.upper() == "GET"
    assert isinstance(http_record.exception, urllib3.exceptions.MaxRetryError)


@pytest.mark.urllib3
def test_urllib3_importerror(httpbin):
    with patch.dict(sys.modules, {"urllib3": None}):
        with httpdbg() as records:
            http = urllib3.PoolManager()
            http.request("GET", f"{httpbin.url}/get")

    assert len(records) == 0
