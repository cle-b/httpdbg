# -*- coding: utf-8 -*-
import sys
from unittest.mock import patch

import aiohttp
import pytest

from httpdbg.server import httpdbg


@pytest.fixture(scope="module", autouse=True)
def skip_incompatible_python():
    if sys.version_info < (3, 7):
        pytest.skip(reason="requires python3.7 or higher")


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.stream is False


@pytest.mark.aiohttp
@pytest.mark.asyncio
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
async def test_aiohttp_request_post_bytes(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{httpbin.url}/post", data=b"abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"abc"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_request_post_str(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{httpbin.url}/post", data="abc")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "3"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"abc"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_request_post_json(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{httpbin.url}/post", json={"a": "bc"})

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "11"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b'{"a": "bc"}'


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_request_post_form(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{httpbin.url}/post", data={"a": "bc", "d": "ef"})

    assert len(records) == 1
    http_record = records[0]

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert {"name": "Content-Length", "value": "9"} in http_record.request.headers
    assert http_record.request.cookies == []
    assert bytes(http_record.request.content) == b"a=bc&d=ef"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_response(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            async with session.put(f"{httpbin.url}/put?azerty", data="def") as resp:
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
async def test_aiohttp_cookies(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
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
async def test_aiohttp_redirect(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.get(f"{httpbin.url}/redirect-to?url={httpbin.url}/get")

    assert len(records) == 2
    assert records[0].url == f"{httpbin.url}/redirect-to?url={httpbin.url}/get"
    assert records[1].url == f"{httpbin.url}/get"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_not_found(httpbin):
    with httpdbg() as records:
        async with aiohttp.ClientSession() as session:
            await session.get(f"{httpbin.url}/404")
    assert len(records) == 1

    http_record = records[0]
    assert records[0].url == f"{httpbin.url}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_exception_asyncclient():
    with httpdbg() as records:
        with pytest.raises(aiohttp.client_exceptions.ClientConnectorError):
            async with aiohttp.ClientSession() as session:
                await session.get("http://f.q.d.1234.n.t.n.e/")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == "http://f.q.d.1234.n.t.n.e/"
    assert http_record.method.upper() == "GET"
    assert isinstance(
        http_record.exception, aiohttp.client_exceptions.ClientConnectorError
    )


@pytest.mark.aiohttp
@pytest.mark.asyncio
async def test_aiohttp_importerror(httpbin):
    with patch.dict(sys.modules, {"aiohttp": None}):
        with httpdbg() as records:
            async with aiohttp.ClientSession() as session:
                await session.get(f"{httpbin.url}/get")

    assert len(records) == 0
