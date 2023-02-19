# -*- coding: utf-8 -*-
import sys
from unittest.mock import patch

import httpx
import pytest

from httpdbg.server import httpdbg


@pytest.fixture(scope="module", autouse=True)
def skip_incompatible_python():
    if sys.version_info < (3, 7):
        pytest.skip(reason="requires python3.7 or higher")


@pytest.mark.httpx
def test_httpx(httpbin):
    with httpdbg() as records:
        httpx.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False


@pytest.mark.httpx
def test_httpx_initiator(httpbin):
    with httpdbg() as records:
        httpx.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == "test_httpx_initiator"
    assert (
        http_record.initiator.long_label
        == "tests/test_hook_httpx.py::test_httpx_initiator"
    )
    assert 'httpx.get(f"{httpbin.url}/get")' in "".join(http_record.initiator.stack)


@pytest.mark.httpx
def test_httpx_request(httpbin):
    with httpdbg() as records:
        httpx.post(f"{httpbin.url}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "content-length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.httpx
def test_httpx_response(httpbin):
    with httpdbg() as records:
        httpx.put(f"{httpbin.url}/put?azerty", content="def")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert {
        "name": "content-type",
        "value": "application/json",
    } in http_record.response.headers
    assert http_record.response.cookies == []
    assert b'"args":{"azerty":""}' in http_record.response.content
    assert b'"data":"def"' in http_record.response.content


@pytest.mark.httpx
def test_httpx_cookies(httpbin):
    with httpdbg() as records:
        httpx.get(
            f"{httpbin.url}/cookies/set/confiture/oignon", cookies={"jam": "strawberry"}
        )

    assert len(records) == 1
    http_record = records[0]

    assert {
        "attributes": [
            {"attr": "/", "name": "path"},
            {"name": "Discard"},
            {"name": "HttpOnly"},
        ],
        "name": "jam",
        "value": "strawberry",
    } in http_record.request.cookies

    assert {
        "attributes": [
            {"attr": "/", "name": "path"},
            {"name": "Discard"},
        ],
        "name": "confiture",
        "value": "oignon",
    } in http_record.response.cookies


@pytest.mark.httpx
@pytest.mark.xfail(reason="stream mode unsupported")
def test_httpx_stream(httpbin):
    with httpdbg() as records:
        httpx.stream("GET", f"{httpbin.url}/get")

    assert len(records) == 1

    http_record = records[0]
    assert http_record.stream is True
    assert http_record.request.content is None
    assert http_record.response.content is None


@pytest.mark.httpx
@pytest.mark.xfail(reason="follow redirects mode unsupported")
def test_httpx_redirect(httpbin):
    with httpdbg() as records:
        httpx.get(
            f"{httpbin.url}/redirect-to?url={httpbin.url}/get", follow_redirects=True
        )

    assert len(records) == 2
    assert records[0].url == f"{httpbin.url}/redirect-to?url={httpbin.url}/get"
    assert records[1].url == f"{httpbin.url}/get"


@pytest.mark.httpx
def test_httpx_not_found(httpbin):
    with httpdbg() as records:
        httpx.get(f"{httpbin.url}/404")

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.httpx
def test_httpx_client(httpbin):
    with httpdbg() as records:
        with httpx.Client() as client:
            client.get(f"{httpbin.url}/get")
            client.post(f"{httpbin.url}/post", content="azerty")

    assert len(records) == 2

    http_record = records[0]
    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False

    http_record = records[1]
    assert http_record.url == f"{httpbin.url}/post"
    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False


@pytest.mark.httpx
def test_httpx_exception():
    with httpdbg() as records:
        with pytest.raises(httpx.ConnectError):
            httpx.get("http://f.q.d.1234.n.t.n.e/")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == "http://f.q.d.1234.n.t.n.e/"
    assert http_record.method.upper() == "GET"
    assert isinstance(http_record.exception, httpx.ConnectError)


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_initiator_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == "test_httpx_initiator_asyncclient"
    assert (
        http_record.initiator.long_label
        == "tests/test_hook_httpx.py::test_httpx_initiator_asyncclient"
    )
    assert 'await client.get(f"{httpbin.url}/get")' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_request_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.post(f"{httpbin.url}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "content-length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_response_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.put(f"{httpbin.url}/put?azerty", content="def")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert {
        "name": "content-type",
        "value": "application/json",
    } in http_record.response.headers
    assert http_record.response.cookies == []
    assert b'"args":{"azerty":""}' in http_record.response.content
    assert b'"data":"def"' in http_record.response.content


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_cookies_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.get(
                f"{httpbin.url}/cookies/set/confiture/oignon",
                cookies={"jam": "strawberry"},
            )

    assert len(records) == 1
    http_record = records[0]

    assert {
        "attributes": [
            {"attr": "/", "name": "path"},
            {"name": "Discard"},
            {"name": "HttpOnly"},
        ],
        "name": "jam",
        "value": "strawberry",
    } in http_record.request.cookies

    assert {
        "attributes": [
            {"attr": "/", "name": "path"},
            {"name": "Discard"},
        ],
        "name": "confiture",
        "value": "oignon",
    } in http_record.response.cookies


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_exception_asyncclient():
    with httpdbg() as records:
        with pytest.raises(httpx.ConnectError):
            async with httpx.AsyncClient() as client:
                await client.get("http://f.q.d.1234.n.t.n.e/")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == "http://f.q.d.1234.n.t.n.e/"
    assert http_record.method.upper() == "GET"
    assert isinstance(http_record.exception, httpx.ConnectError)


@pytest.mark.httpx
def test_httpx_importerror(httpbin):
    with patch.dict(sys.modules, {"httpx": None}):
        with httpdbg() as records:
            httpx.get(f"{httpbin.url}/get")

    assert len(records) == 0
