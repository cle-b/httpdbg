# -*- coding: utf-8 -*-
import json

import pytest
import requests

from httpdbg.hooks.all import httprecord
from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader


@pytest.mark.requests
def test_requests(httpbin_both):
    with httprecord() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.initiator
@pytest.mark.requests
def test_requests_initiator(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httprecord() as records:
            requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == 'requests.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None
    assert 'requests.get(f"{httpbin.url}/get") <===' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.requests
def test_requests_request(httpbin_both):
    with httprecord() as records:
        requests.post(f"{httpbin_both.url}/post", data="abc", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("Content-Length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.requests
def test_requests_response(httpbin_both):
    with httprecord() as records:
        requests.put(f"{httpbin_both.url}/put?azerty=33", data="def", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert (
        HTTPDBGHeader("Content-Type", "application/json")
        in http_record.response.headers
    )
    assert http_record.response.cookies == []
    assert (
        json.loads(http_record.response.content).get("args", {}).get("azerty") == "33"
    )
    assert json.loads(http_record.response.content).get("data") == "def"


@pytest.mark.requests
def test_requests_cookies(httpbin):
    with httprecord() as records:
        requests.get(
            f"{httpbin.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
            allow_redirects=False,
        )

    assert len(records) == 1
    http_record = records[0]

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie(
            "confiture",
            "oignon",
            [
                {"attr": "/", "name": "path"},
            ],
        )
        in http_record.response.cookies
    )


@pytest.mark.requests
def test_requests_cookies_secure(httpbin_secure):
    with httprecord() as records:
        requests.get(
            f"{httpbin_secure.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
            allow_redirects=False,
            verify=False,
        )

    assert len(records) == 1
    http_record = records[0]

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie(
            "confiture", "oignon", [{"attr": "/", "name": "path"}, {"name": "Secure"}]
        )
        in http_record.response.cookies
    )


@pytest.mark.requests
def test_requests_redirect(httpbin_both):
    with httprecord() as records:
        requests.get(
            f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get", verify=False
        )

    assert len(records) == 2
    assert (
        records[0].url == f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get"
    )
    assert records[1].url == f"{httpbin_both.url}/get"


@pytest.mark.requests
def test_requests_not_found(httpbin_both):
    with httprecord() as records:
        requests.get(f"{httpbin_both.url}/404", verify=False)

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin_both.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.requests
def test_requests_session(httpbin_both):
    with httprecord() as records:
        with requests.Session() as session:
            session.get(f"{httpbin_both.url}/get", verify=False)
            session.post(f"{httpbin_both.url}/post", data="azerty", verify=False)

    assert len(records) == 2

    http_record = records[0]
    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"

    http_record = records[1]
    assert http_record.url == f"{httpbin_both.url}/post"
    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.requests
def test_requests_exception():
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httprecord() as records:
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get(url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, requests.exceptions.ConnectionError)


@pytest.mark.requests
def test_requests_get_empty_request_content(httpbin_both):
    with httprecord() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.requests
def test_requests_many_requests(httpbin_both):
    with httprecord() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)
        requests.get(f"{httpbin_both.url}/get/abc", verify=False)
        requests.post(f"{httpbin_both.url}/post", data="abc", verify=False)
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 4

    assert records[0].url == f"{httpbin_both.url}/get"
    assert records[0].request.content == b""
    assert records[1].url == f"{httpbin_both.url}/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == f"{httpbin_both.url}/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == f"{httpbin_both.url}/get"
    assert records[3].request.content == b""


@pytest.mark.requests
def test_requests_many_requests_session(httpbin_both):
    with httprecord() as records:
        with requests.Session() as session:
            session.get(f"{httpbin_both.url}/get", verify=False)
            session.get(f"{httpbin_both.url}/get/abc", verify=False)
            session.post(f"{httpbin_both.url}/post", data="abc", verify=False)
            session.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 4

    assert records[0].url == f"{httpbin_both.url}/get"
    assert records[0].request.content == b""
    assert records[1].url == f"{httpbin_both.url}/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == f"{httpbin_both.url}/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == f"{httpbin_both.url}/get"
    assert records[3].request.content == b""
