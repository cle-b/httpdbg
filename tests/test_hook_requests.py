# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.hooks.all import httpdbg


@pytest.mark.requests
def test_requests(httpbin):
    with httpdbg() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin.url}/get"
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
def test_requests_request(httpbin):
    with httpdbg() as records:
        requests.post(f"{httpbin.url}/post", data="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.requests
def test_requests_response(httpbin):
    with httpdbg() as records:
        requests.put(f"{httpbin.url}/put?azerty", data="def")

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
def test_requests_stream(httpbin):
    request_content = b"key=value"
    response_content = bytes()
    with httpdbg() as records:
        with requests.post(f"{httpbin.url}", data={"key": "value"}) as r:
            for data in r.iter_content():
                response_content += data

    assert response_content != bytes()

    assert len(records) == 1

    http_record = records[0]
    assert http_record.request.content == request_content
    assert http_record.response.content == response_content


@pytest.mark.requests
def test_requests_redirect(httpbin):
    with httpdbg() as records:
        requests.get(f"{httpbin.url}/redirect-to?url={httpbin.url}/get")

    assert len(records) == 2
    assert records[0].url == f"{httpbin.url}/redirect-to?url={httpbin.url}/get"
    assert records[1].url == f"{httpbin.url}/get"


@pytest.mark.requests
def test_requests_not_found(httpbin):
    with httpdbg() as records:
        requests.get(f"{httpbin.url}/404")

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.requests
def test_requests_session(httpbin):
    with httpdbg() as records:
        with requests.Session() as session:
            session.get(f"{httpbin.url}/get")
            session.post(f"{httpbin.url}/post", data="azerty")

    assert len(records) == 2

    http_record = records[0]
    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"

    http_record = records[1]
    assert http_record.url == f"{httpbin.url}/post"
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
