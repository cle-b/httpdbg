# -*- coding: utf-8 -*-
import platform
import sys

import aiohttp
import pytest

from httpdbg.hooks.all import httpdbg


@pytest.fixture(scope="module", autouse=True)
def skip_incompatible_python():
    if sys.version_info < (3, 7):
        pytest.skip(reason="requires python3.7 or higher")


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_initiator(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == "test_aiohttp_initiator"
    assert (
        http_record.initiator.long_label
        == "tests/test_hook_aiohttp.py::test_aiohttp_initiator"
    )
    assert 'await session.get(f"{httpbin.url}/get")' in "".join(
        http_record.initiator.stack
    )


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_request_post_bytes(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.post(f"{httpbin_both.url}/post", data=b"abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"abc"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_request_post_str(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.post(f"{httpbin_both.url}/post", data="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"abc"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_request_post_json(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.post(f"{httpbin_both.url}/post", json={"a": "bc"})

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "11"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b'{"a": "bc"}'


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_request_post_form(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.post(f"{httpbin_both.url}/post", data={"a": "bc", "d": "ef"})

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "9"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"a=bc&d=ef"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_response(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            async with session.put(
                f"{httpbin_both.url}/put?azerty", data="def"
            ) as resp:
                await resp.json()

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


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_cookies(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(
                f"{httpbin.url}/cookies/set/confiture/oignon",
                cookies={"jam": "strawberry"},
            )

    assert len(records) == 2
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


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_cookies_secure(httpbin_secure):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(
                f"{httpbin_secure.url}/cookies/set/confiture/oignon",
                cookies={"jam": "strawberry"},
            )

    assert len(records) == 2
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


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_redirect(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(
                f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get"
            )

    assert len(records) == 2
    assert (
        records[0].url == f"{httpbin_both.url}/redirect-to?url={httpbin_both.url}/get"
    )
    assert records[1].url == f"{httpbin_both.url}/get"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_not_found(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(f"{httpbin_both.url}/404")
    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin_both.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_exception_asyncclient():
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httpdbg() as records:
        with pytest.raises(aiohttp.client_exceptions.ClientConnectorError):
            async with aiohttp.ClientSession() as session:
                await session.get(url_with_unknown_host)

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == url_with_unknown_host
    assert isinstance(
        http_record.exception, aiohttp.client_exceptions.ClientConnectorError
    )


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_get_empty_request_content_asyncclient(httpbin_both):
    with httpdbg() as records:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            await session.get(f"{httpbin_both.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.request.content == b""


@pytest.mark.aiohttp
@pytest.mark.asyncio
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="Async HTTP requests not intercepted on Windows",
)
async def test_aiohttp_many_requests_session_asyncclient():
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
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
