import json

import httpx
import pytest

from httpdbg.hooks.all import httprecord
from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader

from tests.demo_http2 import http2_httpbin_server
from tests.utils import get_free_tcp_port


@pytest.fixture(scope="module")
def httpbin2():
    host = "127.0.0.1"
    port = get_free_tcp_port(host)
    with http2_httpbin_server(host, port) as url:
        yield url


@pytest.mark.h2
def test_h2(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.url == f"{httpbin2}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.protocol == "HTTP/2"


@pytest.mark.initiator
@pytest.mark.h2
def test_h2_initiator(httpbin2, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httprecord() as records:
            client = httpx.Client(http2=True, verify=False)
            client.get(f"{httpbin2}/get")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    initiator = records.initiators[records[0].initiator_id]

    assert initiator.label == 'client.get(f"{httpbin2}/get")'
    assert 'client.get(f"{httpbin2}/get") <===' in "".join(initiator.stack)


@pytest.mark.h2
def test_h2_request(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.post(f"{httpbin2}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("content-length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.h2
def test_h2_response(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.put(f"{httpbin2}/put?azerty=33", content="def")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert (
        HTTPDBGHeader("content-type", "application/json")
        in http_record.response.headers
    )
    assert http_record.response.cookies == []
    assert (
        json.loads(http_record.response.content).get("args", {}).get("azerty") == "33"
    )
    assert json.loads(http_record.response.content).get("data") == "def"


@pytest.mark.h2
def test_h2_cookies(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(
            f"{httpbin2}/cookies/set/confiture/oignon", cookies={"jam": "strawberry"}
        )

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert HTTPDBGCookie("jam", "strawberry") in http_record.request.cookies

    assert (
        HTTPDBGCookie(
            "confiture", "oignon", [{"attr": "/", "name": "path"}, {"name": "Secure"}]
        )
        in http_record.response.cookies
    )


@pytest.mark.h2
def test_h2_client_redirect(httpbin2):
    redirect_url = f"{httpbin2}/redirect-to"
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(
            redirect_url,
            follow_redirects=True,
            params={"url": f"{httpbin2}/get"},
        )

    assert len(records) == 2
    assert records[0].protocol == "HTTP/2"

    assert records[0].url.startswith(redirect_url)
    assert records[1].url == f"{httpbin2}/get"


@pytest.mark.h2
def test_h2_client_not_found(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/404")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert http_record.url == f"{httpbin2}/404"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 404
    assert http_record.reason.upper() == "NOT FOUND"


@pytest.mark.h2
def test_h2_client_get_empty_request_content(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/get")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert http_record.url == f"{httpbin2}/get"
    assert http_record.request.content == b""


@pytest.mark.h2
def test_h2_client_many_requests(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/get")
        client.get(f"{httpbin2}/get/abc")
        client.post(f"{httpbin2}/post", data="abc")
        client.get(f"{httpbin2}/get")

    assert len(records) == 4

    assert records[0].url == f"{httpbin2}/get"
    assert records[0].request.content == b""
    assert records[0].protocol == "HTTP/2"
    assert records[1].url == f"{httpbin2}/get/abc"
    assert records[1].request.content == b""
    assert records[1].protocol == "HTTP/2"
    assert records[2].url == f"{httpbin2}/post"
    assert records[2].request.content == b"abc"
    assert records[2].protocol == "HTTP/2"
    assert records[3].url == f"{httpbin2}/get"
    assert records[3].request.content == b""
    assert records[3].protocol == "HTTP/2"


@pytest.mark.h2
def test_h2_client_many_requests_session(httpbin2):
    with httprecord() as records:
        with httpx.Client(http2=True, verify=False) as session:
            session.get(f"{httpbin2}/get")
            session.get(f"{httpbin2}/get/abc")
            session.post(f"{httpbin2}/post", data="abc")
            session.get(f"{httpbin2}/get")

    assert len(records) == 4

    assert records[0].url == f"{httpbin2}/get"
    assert records[0].request.content == b""
    assert records[0].protocol == "HTTP/2"
    assert records[1].url == f"{httpbin2}/get/abc"
    assert records[1].request.content == b""
    assert records[1].protocol == "HTTP/2"
    assert records[2].url == f"{httpbin2}/post"
    assert records[2].request.content == b"abc"
    assert records[2].protocol == "HTTP/2"
    assert records[3].url == f"{httpbin2}/get"
    assert records[3].request.content == b""
    assert records[3].protocol == "HTTP/2"


@pytest.mark.h2
@pytest.mark.asyncio
async def test_h2_client_asyncclient(httpbin2):
    with httprecord() as records:
        async with httpx.AsyncClient(http2=True, verify=False) as client:
            await client.get(f"{httpbin2}/get")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.protocol == "HTTP/2"

    assert http_record.url == f"{httpbin2}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"


@pytest.mark.server_requests
@pytest.mark.h2
def test_h2_server(httpbin2):
    with httprecord(server=True) as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/get")

    assert len(records) == 2
    assert records[0].is_client is True
    assert records[1].is_client is False

    for http_record in records:
        assert http_record.url == f"{httpbin2}/get"
        assert http_record.method.upper() == "GET"
        assert http_record.status_code == 200
        assert http_record.reason.upper() == "OK"
        assert http_record.protocol == "HTTP/2"


@pytest.mark.server_requests
@pytest.mark.h2
def test_h2_server_only(httpbin2):
    with httprecord(client=False, server=True) as records:
        client = httpx.Client(http2=True, verify=False)
        client.get(f"{httpbin2}/get")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.is_client is False
    assert http_record.url == f"{httpbin2}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert http_record.protocol == "HTTP/2"


@pytest.mark.server_requests
@pytest.mark.h2
def test_h2_server_request(httpbin2):
    with httprecord(client=False, server=True) as records:
        client = httpx.Client(http2=True, verify=False)
        client.post(f"{httpbin2}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.is_client is False
    assert http_record.protocol == "HTTP/2"

    assert http_record.method.upper() == "POST"
    assert http_record.status_code == 200

    assert HTTPDBGHeader("content-length", "3") in http_record.request.headers
    assert http_record.request.cookies == []
    assert http_record.request.content == b"abc"


@pytest.mark.server_requests
@pytest.mark.h2
def test_h2_server_response(httpbin2):
    with httprecord(client=False, server=True) as records:
        client = httpx.Client(http2=True, verify=False)
        client.put(f"{httpbin2}/put?azerty=33", content="def")

    assert len(records) == 1
    http_record = records[0]
    assert http_record.is_client is False
    assert http_record.protocol == "HTTP/2"

    assert http_record.method.upper() == "PUT"
    assert http_record.status_code == 200

    assert (
        HTTPDBGHeader("content-type", "application/json")
        in http_record.response.headers
    )
    assert http_record.response.cookies == []
    assert (
        json.loads(http_record.response.content).get("args", {}).get("azerty") == "33"
    )
    assert json.loads(http_record.response.content).get("data") == "def"
