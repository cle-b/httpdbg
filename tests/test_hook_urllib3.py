# -*- coding: utf-8 -*-
import pytest
import urllib3

from httpdbg.hooks.all import httpdbg


@pytest.mark.urllib3
def test_urllib3(httpbin_both):
    with httpdbg() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.urllib3
def test_urllib3_initiator(httpbin):
    with httpdbg() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
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
def test_urllib3_request(httpbin_both):
    with httpdbg() as records:
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

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.urllib3
def test_urllib3_response(httpbin_both):
    with httpdbg() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "PUT",
                f"{httpbin_both.url}/put?azerty",
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
        with urllib3.PoolManager() as http:
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
def test_urllib3_cookies_secure(httpbin_secure):
    with httpdbg() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request(
                "GET",
                f"{httpbin_secure.url}/cookies/set/confiture/oignon",
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
        "attributes": [{"attr": "/", "name": "path"}, {"name": "Secure"}],
        "name": "confiture",
        "value": "oignon",
    } in http_record.response.cookies


@pytest.mark.urllib3
def test_urllib3_redirect(httpbin_both):
    with httpdbg() as records:
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
    with httpdbg() as records:
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

    with httpdbg() as records:
        with pytest.raises(urllib3.exceptions.MaxRetryError):
            with urllib3.PoolManager() as http:
                http.request("GET", url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, urllib3.exceptions.MaxRetryError)


@pytest.mark.urllib3
def test_urllib3_get_empty_request_content(httpbin_both):
    with httpdbg() as records:
        with urllib3.PoolManager(cert_reqs="CERT_NONE") as http:
            http.request("GET", f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""
