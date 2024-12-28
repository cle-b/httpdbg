# -*- coding: utf-8 -*-
import json
from packaging import version
import pkg_resources

import pytest
import urllib3

from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader
from httpdbg.hooks.all import httprecord


@pytest.mark.urllib3
def test_urllib3(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.initiator
@pytest.mark.urllib3
def test_urllib3_initiator(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httprecord() as records:
            with urllib3.PoolManager() as http:
                http.request("GET", f"{httpbin.url}/get")
            with urllib3.HTTPConnectionPool(f"{httpbin.url[7:]}") as http:
                http.request("GET", "/get")

    assert len(records) == 2

    assert (
        records.initiators[records[0].initiator_id].label
        == 'http.request("GET", f"{httpbin.url}/get")'
    )
    assert 'http.request("GET", f"{httpbin.url}/get") <===' in "".join(
        records.initiators[records[0].initiator_id].stack
    )

    assert (
        records.initiators[records[1].initiator_id].label
        == 'http.request("GET", "/get")'
    )
    assert 'http.request("GET", "/get") <===' in "".join(
        records.initiators[records[1].initiator_id].stack
    )


@pytest.mark.initiator
@pytest.mark.urllib3
def test_urllib3_initiator_secure(httpbin_secure):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_secure.url}/get")
        with urllib3.HTTPSConnectionPool(
            f"{httpbin_secure.url[8:]}", cert_reqs="CERT_NONE"
        ) as http:
            http.request("GET", "/get")

    assert len(records) == 2

    assert (
        records.initiators[records[0].initiator_id].label
        == 'http.request("GET", f"{httpbin_secure.url}/get")'
    )
    assert 'http.request("GET", f"{httpbin_secure.url}/get") <===' in "".join(
        records.initiators[records[0].initiator_id].stack
    )

    assert (
        records.initiators[records[1].initiator_id].label
        == 'http.request("GET", "/get")'
    )
    assert 'http.request("GET", "/get") <===' in "".join(
        records.initiators[records[1].initiator_id].stack
    )


@pytest.mark.urllib3
def test_urllib3_request(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "POST",
                f"{httpbin_both.url}/post",
                body="abc",
                headers={"Content-Length": "3"},
            )

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("Content-Length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.urllib3
def test_urllib3_response(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "PUT",
                f"{httpbin_both.url}/put?azerty=33",
                body="def",
                headers={"Content-Length": "3"},
            )

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


@pytest.mark.urllib3
def test_urllib3_cookies(httpbin):
    with httprecord() as records:
        with urllib3.PoolManager() as http:
            http.request(
                "GET",
                f"{httpbin.url}/cookies/set/confiture/oignon",
                headers={"Content-Length": "3", "Cookie": "jam=strawberry"},
                redirect=False,
            )

    assert len(records) == 1
    http_record = records[0]

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie("confiture", "oignon", [{"attr": "/", "name": "path"}])
        in http_record.response.cookies
    )


@pytest.mark.urllib3
def test_urllib3_cookies_secure(httpbin_secure):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "GET",
                f"{httpbin_secure.url}/cookies/set/confiture/oignon",
                headers={"Content-Length": "3", "Cookie": "jam=strawberry"},
                redirect=False,
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


@pytest.mark.urllib3
def test_urllib3_redirect(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "GET", f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get"
            )

    assert len(records) == 2
    assert (
        records[0].url == f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get"
    )
    assert records[1].url == f"{httpbin_both.url}/get"


@pytest.mark.urllib3
def test_urllib3_not_found(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_both.url}/404")

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin_both.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.urllib3
def test_urllib3_exception():
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httprecord() as records:
        with pytest.raises(urllib3.exceptions.MaxRetryError):
            with urllib3.PoolManager() as http:
                http.request("GET", url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, urllib3.exceptions.MaxRetryError)


@pytest.mark.urllib3
def test_urllib3_get_empty_request_content(httpbin_both):
    with httprecord() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.initiator
@pytest.mark.urllib3
@pytest.mark.skipif(
    version.parse(pkg_resources.get_distribution("urllib3").version)
    < version.parse("2.0.0"),
    reason="only urllib3 v2",
)
def test_urllib3_v2_request(httpbin):
    with httprecord() as records:
        urllib3.request("GET", f"{httpbin.url}/get")

    assert len(records) == 1

    assert (
        records.initiators[records[0].initiator_id].label
        == 'urllib3.request("GET", f"{httpbin.url}/get")'
    )
    assert 'urllib3.request("GET", f"{httpbin.url}/get") <===' in "".join(
        records.initiators[records[0].initiator_id].stack
    )
