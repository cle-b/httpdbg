import httpx
import pytest
import requests

from httpdbg.hooks.all import httprecord
from httpdbg.hooks.recordhttp1 import HTTP1Record
from httpdbg.hooks.recordhttp2 import HTTP2Record
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


@pytest.mark.serialization
def test_serialization_http1record(httpbin):
    with httprecord() as records:
        requests.get(
            f"{httpbin.url}/cookies/set/confiture/oignon",
            cookies={"jam": "strawberry"},
            allow_redirects=False,
        )

    assert len(records) == 1
    http_record = records[0]
    http_record_copy = HTTP1Record.from_json(http_record.to_json())

    assert HTTPDBGCookie("jam", "strawberry") in http_record_copy.request.cookies

    assert (
        HTTPDBGCookie(
            "confiture",
            "oignon",
            [
                {"attr": "/", "name": "path"},
            ],
        )
        in http_record_copy.response.cookies
    )

    assert http_record_copy == http_record


@pytest.mark.serialization
def test_serialization_http2record(httpbin2):
    with httprecord() as records:
        client = httpx.Client(http2=True, verify=False)
        client.post(f"{httpbin2}/post", content="abc")

    assert len(records) == 1
    http_record = records[0]
    http_record_copy = HTTP2Record.from_json(http_record.to_json())

    assert http_record_copy.protocol == "HTTP/2"

    assert http_record_copy.method.upper() == "POST"
    assert http_record_copy.status_code == 200

    assert HTTPDBGHeader("content-length", "3") in http_record_copy.request.headers
    assert http_record_copy.request.cookies == []
    assert http_record_copy.request.content == b"abc"

    assert http_record_copy.last_update == http_record.last_update

    assert http_record_copy == http_record


@pytest.mark.serialization
def test_serialization_compatibility():
    http1record = HTTP1Record("a", "b")
    http2record = HTTP2Record("a", "b")
    assert not (http1record == http2record)
    assert not (http2record == http1record)
