# -*- coding: utf-8 -*-
import requests

import pytest

from httpdbg.hooks.all import httprecord
from httpdbg.server import httpdbg_srv

from tests.utils import get_request_content_up
from tests.utils import get_request_details


@pytest.mark.api
def test_api_requests_one_request(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get")

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"


@pytest.mark.api
def test_api_requests_two_requests(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get?abc")
            requests.get(httpbin.url + "/get?def")

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get?abc"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get?def"


@pytest.mark.api
def test_api_requests_netloc(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get?abc")
        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get?abc"
    assert reqs[list(reqs.keys())[0]]["netloc"] == httpbin.url
    assert reqs[list(reqs.keys())[0]]["urlext"] == "/get?abc"


@pytest.mark.api
def test_api_requests_protocol(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get?abc")
        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["protocol"] == "HTTP/1.1"


@pytest.mark.api
def test_api_request_by_id(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get?abc")
            requests.get(httpbin.url + "/get?def")

        ret0 = get_request_details(httpdbg_port, 0)
        ret1 = get_request_details(httpdbg_port, 1)

    assert ret0.status_code == 200
    assert ret0.json()["url"] == httpbin.url + "/get?abc"

    assert ret1.status_code == 200
    assert ret1.json()["url"] == httpbin.url + "/get?def"


@pytest.mark.api
def test_api_request_by_id_not_exists(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/get?abc")
            requests.get(httpbin.url + "/get?def")

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/request/999")

    assert ret.status_code == 404


@pytest.mark.api
def test_api_get_request_get(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/")
            requests.get(httpbin.url + "/get")

        ret = get_request_details(httpdbg_port, 1)

        path_to_content = ret.json()["response"]["body"]["path"]
        req_response_content = requests.get(
            f"http://{httpdbg_host}:{httpdbg_port}{path_to_content}"
        )

    # headers
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get"
    assert ret.json()["method"] == "GET"
    assert ret.json()["status_code"] == 200
    assert ret.json()["reason"] == "OK"

    # request
    assert {"name": "Connection", "value": "keep-alive"} in ret.json()["request"][
        "headers"
    ]
    assert ret.json()["request"]["cookies"] == []

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "download"

    assert req_response_content.status_code == 200


@pytest.mark.api
def test_api_get_request_post(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.get(httpbin.url + "/")
            requests.post(httpbin.url + "/post", data=b"data to post")

        ret = get_request_details(httpdbg_port, 1)

        path_to_content = ret.json()["request"]["body"]["path"]
        req_request_content = requests.get(
            f"http://{httpdbg_host}:{httpdbg_port}{path_to_content}"
        )

        path_to_content = ret.json()["response"]["body"]["path"]
        req_response_content = requests.get(
            f"http://{httpdbg_host}:{httpdbg_port}{path_to_content}"
        )

    # headers
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/post"
    assert ret.json()["method"] == "POST"
    assert ret.json()["status_code"] == 200
    assert ret.json()["reason"] == "OK"

    # request
    assert {"name": "Connection", "value": "keep-alive"} in ret.json()["request"][
        "headers"
    ]
    assert ret.json()["request"]["cookies"] == []
    assert ret.json()["request"]["body"]["filename"] == "upload"

    assert req_request_content.text == "data to post"

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "download"

    assert req_response_content.status_code == 200


@pytest.mark.api
def test_api_get_request_get_status_404(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            ret = requests.get(httpbin.url + "/abc")
        assert ret.status_code == 404

        ret = get_request_details(httpdbg_port, 0)

    assert ret.json()["url"] == httpbin.url + "/abc"
    assert ret.json()["status_code"] == 404
    assert ret.json()["reason"] == "NOT FOUND"


@pytest.mark.api
def test_api_get_request_connection_error(httpbin, httpdbg_host, httpdbg_port):
    url_with_unknown_host = "http://f.q.d.1234.n.t.n.e/hello?a=b"

    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            with pytest.raises(requests.exceptions.ConnectionError):
                requests.get(url_with_unknown_host)

        ret = get_request_details(httpdbg_port, 0)

    assert ret.json()["url"] == url_with_unknown_host
    assert ret.json()["status_code"] == -1
    assert ret.json()["reason"] == "ConnectionError"


@pytest.mark.api
def test_api_get_request_content_up_text(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            requests.post(httpbin.url + "/post", data={"a": 1, "b": 2})
            requests.post(httpbin.url + "/post", data="hello")

        ret0 = get_request_content_up(httpdbg_port, 0)
        ret1 = get_request_content_up(httpdbg_port, 1)

    assert ret0.status_code == 200
    assert ret0.content == b"a=1&b=2"

    assert ret1.status_code == 200
    assert ret1.content == b"hello"


@pytest.mark.api
@pytest.mark.cookies
def test_cookies_request(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            session = requests.session()
            session.cookies.set("COOKIE_NAME", "the-cookie-works")
            session.get(httpbin.url + "/get")

        ret = get_request_details(httpdbg_port, 0)

    cookies = ret.json()["request"]["cookies"]
    assert len(cookies) == 1
    assert cookies[0]["name"] == "COOKIE_NAME"
    assert cookies[0]["value"] == "the-cookie-works"


@pytest.mark.api
@pytest.mark.cookies
def test_cookies_response(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            session = requests.session()
            session.get(
                httpbin.url + "/cookies/set/THE_COOKIE_NAME/THE_COOKIE_VALUE",
                allow_redirects=False,
            )

        ret = get_request_details(httpdbg_port, 0)

    cookies = ret.json()["response"]["cookies"]
    assert len(cookies) == 1
    assert cookies[0]["name"] == "THE_COOKIE_NAME"
    assert cookies[0]["value"] == "THE_COOKIE_VALUE"
    assert {"name": "path", "attr": "/"} in cookies[0]["attributes"]
