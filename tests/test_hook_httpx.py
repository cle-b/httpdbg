# -*- coding: utf-8 -*-
import platform
import sys
import urllib.parse

import httpx
import pytest

from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader
from httpdbg.hooks.all import httpdbg


@pytest.fixture(scope="module", autouse=True)
def skip_incompatible_python():
    if sys.version_info < (3, 7):
        pytest.skip(reason="requires python3.7 or higher")


@pytest.mark.httpx
def test_httpx(httpbin_both):
    with httpdbg() as records:
        httpx.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.initiator
@pytest.mark.httpx
def test_httpx_initiator(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            httpx.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == 'httpx.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None
    assert 'httpx.get(f"{httpbin.url}/get") <===' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.httpx
def test_httpx_request(httpbin_both):
    with httpdbg() as records:
        httpx.post(f"{httpbin_both.url}/post", content="abc", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("Content-Length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.httpx
def test_httpx_response(httpbin_both):
    with httpdbg() as records:
        httpx.put(f"{httpbin_both.url}/put?azerty", content="def", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert (
        HTTPDBGHeader("Content-Type", "application/json")
        in http_record.response.headers
    )
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

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie("confiture", "oignon", [{"attr": "/", "name": "path"}])
        in http_record.response.cookies
    )


@pytest.mark.httpx
def test_httpx_cookies_secure(httpbin_secure):
    with httpdbg() as records:
        httpx.get(
            f"{httpbin_secure.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
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
def test_httpx_redirect(httpbin_both):
    redirect_url = f"{httpbin_both.url}/redirect-to?{urllib.parse.urlencode({'url': httpbin_both.url})}/get"
    with httpdbg() as records:
        httpx.get(
            redirect_url,
            follow_redirects=True,
            verify=False,
        )

    assert len(records) == 2
    assert records[0].url == redirect_url
    assert records[1].url == f"{httpbin_both.url}/get"


@pytest.mark.httpx
def test_httpx_not_found(httpbin_both):
    with httpdbg() as records:
        httpx.get(f"{httpbin_both.url}/404", verify=False)

    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin_both.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.httpx
def test_httpx_client(httpbin_both):
    with httpdbg() as records:
        with httpx.Client(verify=False) as client:
            client.get(f"{httpbin_both.url}/get")
            client.post(f"{httpbin_both.url}/post", content="azerty")

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
def test_httpx_get_empty_request_content(httpbin_both):
    with httpdbg() as records:
        httpx.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.httpx
def test_httpx_many_requests():
    with httpdbg() as records:
        httpx.get("https://httpbin.org/get")
        httpx.get("https://httpbin.org/get/abc")
        httpx.post("https://httpbin.org/post", data="abc")
        httpx.get("https://httpbin.org/get")

    assert len(records) == 4

    assert records[0].url == "https://httpbin.org/get"
    assert records[0].request.content == b""
    assert records[1].url == "https://httpbin.org/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == "https://httpbin.org/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == "https://httpbin.org/get"
    assert records[3].request.content == b""


@pytest.mark.httpx
def test_httpx_many_requests_session():
    with httpdbg() as records:
        with httpx.Client() as session:
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


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_asyncclient(httpbin_both):
    with httpdbg() as records:
        async with httpx.AsyncClient(verify=False) as client:
            await client.get(f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.initiator
@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_initiator_asyncclient(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            async with httpx.AsyncClient() as client:
                await client.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == 'await client.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None
    assert 'await client.get(f"{httpbin.url}/get") <===' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_request_asyncclient(httpbin_both):
    with httpdbg() as records:
        async with httpx.AsyncClient(verify=False) as client:
            await client.post(f"{httpbin_both.url}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("Content-Length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_response_asyncclient(httpbin_both):
    with httpdbg() as records:
        async with httpx.AsyncClient(verify=False) as client:
            await client.put(f"{httpbin_both.url}/put?azerty", content="def")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert (
        HTTPDBGHeader("Content-Type", "application/json")
        in http_record.response.headers
    )
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

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie("confiture", "oignon", [{"attr": "/", "name": "path"}])
        in http_record.response.cookies
    )


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_cookies_asyncclient_secure(httpbin_secure):
    with httpdbg() as records:
        async with httpx.AsyncClient(verify=False) as client:
            await client.get(
                f"{httpbin_secure.url}/cookies/set/confiture/oignon",
                cookies={"jam": "strawberry"},
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


@pytest.mark.httpx
@pytest.mark.asyncio
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


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_get_empty_request_content_asyncclient(httpbin_both):
    with httpdbg() as records:
        async with httpx.AsyncClient(verify=False) as client:
            await client.get(f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.httpx
@pytest.mark.asyncio
async def test_httpx_many_requests_session_asyncclient():
    with httpdbg() as records:
        async with httpx.AsyncClient() as session:
            await session.get("https://httpbin.org/get")
            await session.get("https://httpbin.org/get/abc")
            await session.post("https://httpbin.org/post", data="abc")
            await session.get("https://httpbin.org/get")

    assert len(records) == 4

    assert records[0].url == "https://httpbin.org/get"
    assert records[0].request.content == b""
    assert records[1].url == "https://httpbin.org/get/abc"
    assert records[1].request.content == b""
    assert records[2].url == "https://httpbin.org/post"
    assert records[2].request.content == b"abc"
    assert records[3].url == "https://httpbin.org/get"
    assert records[3].request.content == b""
