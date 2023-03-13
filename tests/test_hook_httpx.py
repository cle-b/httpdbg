# -*- coding: utf-8 -*-
import platform
import sys

import httpx
import pytest

from httpdbg.hooks.all import httpdbg


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

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
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
        "name": "Content-Type",
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


@pytest.mark.httpx
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="An established connection was aborted by the software in your host machine",
)
def test_httpx_stream(httpbin):
    request_content = b"key=value"
    response_content = bytes()
    with httpdbg() as records:
        with httpx.stream("POST", f"{httpbin.url}", data={"key": "value"}) as r:
            for data in r.iter_bytes():
                response_content += data

    assert response_content != bytes()

    assert len(records) == 1

    http_record = records[0]
    assert http_record.request.content == request_content
    assert http_record.response.content == response_content


@pytest.mark.httpx
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

    http_record = records[1]
    assert http_record.url == f"{httpbin.url}/post"
    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.httpx
def test_httpx_exception():
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httpdbg() as records:
        with pytest.raises(httpx.ConnectError):
            httpx.get(url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, httpx.ConnectError)


@pytest.mark.httpx
@pytest.mark.asyncio
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
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


@pytest.mark.httpx
@pytest.mark.asyncio
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
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
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_httpx_request_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.post(f"{httpbin.url}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.httpx
@pytest.mark.asyncio
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_httpx_response_asyncclient(httpbin):
    with httpdbg() as records:
        async with httpx.AsyncClient() as client:
            await client.put(f"{httpbin.url}/put?azerty", content="def")

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


@pytest.mark.httpx
@pytest.mark.asyncio
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
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


@pytest.mark.httpx
@pytest.mark.asyncio
@pytest.mark.xfail(
    (platform.system().lower() == "windows") and (sys.version_info >= (3, 8)),
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_httpx_exception_asyncclient():
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httpdbg() as records:
        with pytest.raises(httpx.ConnectError):
            async with httpx.AsyncClient() as client:
                await client.get(url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(http_record.exception, httpx.ConnectError)
