# -*- coding: utf-8 -*-
import platform
import pytest
import requests

from httpdbg.hooks.all import httpdbg


@pytest.mark.requests
def test_requests(httpbin_both):
    with httpdbg() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.requests
def test_requests_initiator(httpbin):
    with httpdbg() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == "test_requests_initiator"
    assert (
        http_record.initiator.long_label
        == "tests/test_hook_requests.py::test_requests_initiator"
    )
    assert 'requests.get(f"{httpbin.url}/get")' in "".join(http_record.initiator.stack)


@pytest.mark.requests
def test_requests_request(httpbin_both):
    with httpdbg() as records:
        requests.post(f"{httpbin_both.url}/post", data="abc", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.requests
def test_requests_response(httpbin_both):
    with httpdbg() as records:
        requests.put(f"{httpbin_both.url}/put?azerty", data="def", verify=False)

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


@pytest.mark.requests
def test_requests_cookies(httpbin):
    with httpdbg() as records:
        requests.get(
            f"{httpbin.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
            allow_redirects=False,
        )

    assert len(records) == 1

    http_record = records[0]
    assert {
        "name": "jam",
        "value": "strawberry",
    } in http_record.request.cookies

    assert {
        "attributes": [
            {"attr": "/", "name": "path"},
        ],
        "name": "confiture",
        "value": "oignon",
    } in http_record.response.cookies


@pytest.mark.requests
def test_requests_cookies_secure(httpbin_secure):
    with httpdbg() as records:
        requests.get(
            f"{httpbin_secure.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
            allow_redirects=False,
            verify=False,
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


@pytest.mark.requests
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="An established connection was aborted by the software in your host machine",
)
def test_requests_stream(httpbin_both):
    request_content = b"key=value"
    response_content = bytes()
    with httpdbg() as records:
        with requests.post(
            f"{httpbin_both.url}", data={"key": "value"}, verify=False
        ) as r:
            for data in r.iter_content():
                response_content += data

    assert response_content != bytes()

    assert len(records) == 1

    http_record = records[0]
    assert http_record.request.content == request_content
    assert http_record.response.content == response_content


@pytest.mark.requests
def test_requests_redirect(httpbin_both):
    with httpdbg() as records:
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
    with httpdbg() as records:
        requests.get(f"{httpbin_both.url}/404", verify=False)

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin_both.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.requests
def test_requests_session(httpbin_both):
    with httpdbg() as records:
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

    with httpdbg() as records:
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get(url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, requests.exceptions.ConnectionError)


@pytest.mark.requests
def test_requests_get_empty_request_content(httpbin_both):
    with httpdbg() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.requests
def test_requests_many_requests():
    with httpdbg() as records:
        requests.get("https://httpbin.org/get")
        requests.get("https://httpbin.org/get/abc")
        requests.post("https://httpbin.org/post", data="abc")
        requests.get("https://httpbin.org/get")

    assert len(records) == 4

    assert records[0].url == "https://httpbin.org/get"
    assert records[0].request.content == b""
    assert records[1].url == "https://httpbin.org/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == "https://httpbin.org/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == "https://httpbin.org/get"
    assert records[3].request.content == b""


@pytest.mark.requests
def test_requests_many_requests_session():
    with httpdbg() as records:
        with requests.Session() as session:
            session.get("https://httpbin.org/get")
            session.get("https://httpbin.org/get/abc")
            session.post("https://httpbin.org/post", data="abc")
            session.get("https://httpbin.org/get")

    assert len(records) == 4

    assert records[0].url == "https://httpbin.org/get"
    assert records[0].request.content == b""
    assert records[1].url == "https://httpbin.org/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == "https://httpbin.org/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == "https://httpbin.org/get"
    assert records[3].request.content == b""
