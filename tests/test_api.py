# -*- coding: utf-8 -*-
import requests

import pytest

from utils import _run_under_httpdbg
from utils import _run_httpdbg_server
from utils import get_request_content_up
from utils import get_request_details

# TODO always execute stop_httpdbg even in case of error


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_one_request(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"

    server.shutdown()


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_two_requests(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get/abc"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get/def"

    server.shutdown()


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_netloc(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get/abc"
    assert reqs[list(reqs.keys())[0]]["netloc"] == httpbin.url
    assert reqs[list(reqs.keys())[0]]["urlext"] == "/get/abc"

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = get_request_details(server.port, 0)
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get/abc"

    ret = get_request_details(server.port, 1)
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get/def"

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id_not_exists(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/request/999")
    assert ret.status_code == 404

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/")
        requests.get(httpbin.url + "/get")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = get_request_details(server.port, 1)

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
    path_to_content = ret.json()["response"]["body"]["path"]
    assert (
        requests.get(f"http://127.0.0.1:{server.port}/{path_to_content}").status_code
        == 200
    )

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_post(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/")
        requests.post(httpbin.url + "/post", data=b"data to post")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = get_request_details(server.port, 1)

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
    path_to_content = ret.json()["request"]["body"]["path"]
    assert (
        requests.get(f"http://127.0.0.1:{server.port}/{path_to_content}").text
        == "data to post"
    )

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "download"
    path_to_content = ret.json()["response"]["body"]["path"]
    assert (
        requests.get(f"http://127.0.0.1:{server.port}/{path_to_content}").status_code
        == 200
    )

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get_status_404(httpbin):
    def _test(httpbin):
        ret = requests.get(httpbin.url + "/get/abc")
        assert ret.status_code == 404

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = get_request_details(server.port, 0)

    assert ret.json()["url"] == httpbin.url + "/get/abc"
    assert ret.json()["status_code"] == 404
    assert ret.json()["reason"] == "NOT FOUND"

    server.shutdown()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_connection_error(httpbin):
    def _test(httpbin):
        try:
            requests.get("http://u.r.l.ooooooo/get/abc")
        except requests.exceptions.ConnectionError:
            pass

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = get_request_details(server.port, 0)

    assert ret.json()["url"] == "http://u.r.l.ooooooo/get/abc"
    assert ret.json()["status_code"] == -1
    assert ret.json()["reason"] == "ConnectionError"

    server.shutdown()


@pytest.mark.api
@pytest.mark.request_content
def test_api_get_request_content_up_text(httpbin):
    def _test(httpbin):
        requests.post(httpbin.url + "/post", data={"a": 1, "b": 2})
        requests.post(httpbin.url + "/post", data="hello")

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret0 = get_request_content_up(server.port, 0)
    ret1 = get_request_content_up(server.port, 1)

    assert ret0.status_code == 200
    assert ret0.content == b"a=1&b=2"

    assert ret1.status_code == 200
    assert ret1.content == b"hello"

    server.shutdown()
