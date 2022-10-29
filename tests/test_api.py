# -*- coding: utf-8 -*-
import requests
import pytest

from httpdbg.server import httpdbg_hook
from httpdbg.server import httpdbg_srv

from utils import get_request_content_up
from utils import get_request_details


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_one_request(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/get")

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_two_requests(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get/abc"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get/def"


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_netloc(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/get/abc")

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get/abc"
    assert reqs[list(reqs.keys())[0]]["netloc"] == httpbin.url
    assert reqs[list(reqs.keys())[0]]["urlext"] == "/get/abc"


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    with httpdbg_srv(httpdbg_port):
        ret0 = get_request_details(httpdbg_port, 0)
        ret1 = get_request_details(httpdbg_port, 1)

    assert ret0.status_code == 200
    assert ret0.json()["url"] == httpbin.url + "/get/abc"

    assert ret1.status_code == 200
    assert ret1.json()["url"] == httpbin.url + "/get/def"


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id_not_exists(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/request/999")

    assert ret.status_code == 404


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/")
        requests.get(httpbin.url + "/get")

    with httpdbg_srv(httpdbg_port):
        ret = get_request_details(httpdbg_port, 1)

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

    with httpdbg_srv(httpdbg_port):
        path_to_content = ret.json()["response"]["body"]["path"]
        status_code = requests.get(
            f"http://127.0.0.1:{httpdbg_port}/{path_to_content}"
        ).status_code

    assert status_code == 200


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_post(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.get(httpbin.url + "/")
        requests.post(httpbin.url + "/post", data=b"data to post")

    with httpdbg_srv(httpdbg_port):
        ret = get_request_details(httpdbg_port, 1)

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

    with httpdbg_srv(httpdbg_port):
        path_to_content = ret.json()["request"]["body"]["path"]
        text = requests.get(f"http://127.0.0.1:{httpdbg_port}/{path_to_content}").text

    assert text == "data to post"

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "download"

    with httpdbg_srv(httpdbg_port):
        path_to_content = ret.json()["response"]["body"]["path"]
        status_code = requests.get(
            f"http://127.0.0.1:{httpdbg_port}/{path_to_content}"
        ).status_code
    assert status_code == 200


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get_status_404(httpbin, httpdbg_port):
    with httpdbg_hook():
        ret = requests.get(httpbin.url + "/get/abc")
    assert ret.status_code == 404

    with httpdbg_srv(httpdbg_port):
        ret = get_request_details(httpdbg_port, 0)

    assert ret.json()["url"] == httpbin.url + "/get/abc"
    assert ret.json()["status_code"] == 404
    assert ret.json()["reason"] == "NOT FOUND"


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_connection_error(httpbin, httpdbg_port):
    with httpdbg_hook():
        try:
            requests.get("http://u.r.l.ooooooo/get/abc")
        except requests.exceptions.ConnectionError:
            pass

    with httpdbg_srv(httpdbg_port):
        ret = get_request_details(httpdbg_port, 0)

    assert ret.json()["url"] == "http://u.r.l.ooooooo/get/abc"
    assert ret.json()["status_code"] == -1
    assert ret.json()["reason"] == "ConnectionError"


@pytest.mark.api
@pytest.mark.request_content
def test_api_get_request_content_up_text(httpbin, httpdbg_port):
    with httpdbg_hook():
        requests.post(httpbin.url + "/post", data={"a": 1, "b": 2})
        requests.post(httpbin.url + "/post", data="hello")

    with httpdbg_srv(httpdbg_port):
        ret0 = get_request_content_up(httpdbg_port, 0)
        ret1 = get_request_content_up(httpdbg_port, 1)

    assert ret0.status_code == 200
    assert ret0.content == b"a=1&b=2"

    assert ret1.status_code == 200
    assert ret1.content == b"hello"
