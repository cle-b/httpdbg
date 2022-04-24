# -*- coding: utf-8 -*-
import requests

import pytest

from utils import _run_under_httpdbg


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_one_request(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[0]["url"] == httpbin.url + "/get"


@pytest.mark.api
@pytest.mark.requests
def test_api_requests_two_requests(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[0]["url"] == httpbin.url + "/get/abc"
    assert reqs[1]["url"] == httpbin.url + "/get/def"


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/0")
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get/abc"

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/1")
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get/def"

    stop_httpdbg()


@pytest.mark.api
@pytest.mark.request
def test_api_request_by_id_not_exists(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/999")
    assert ret.status_code == 404

    stop_httpdbg()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/")
        requests.get(httpbin.url + "/get")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/1")

    # headers
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get"
    assert ret.json()["method"] == "GET"
    assert ret.json()["protocol"] == "http"
    assert ret.json()["status"] == {"code": 200, "message": "OK"}

    # request
    assert {"name": "Connection", "value": "keep-alive"} in ret.json()["request"][
        "headers"
    ]
    assert ret.json()["request"]["cookies"] == []
    assert "body" not in ret.json()["request"]

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "get"
    path_to_content = ret.json()["response"]["body"]["path"]
    assert (
        requests.get(
            f"http://127.0.0.1:{current_httpdbg_port}/{path_to_content}"
        ).status_code
        == 200
    )

    stop_httpdbg()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_post(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/")
        requests.post(httpbin.url + "/post", data="data to post")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/1")

    # headers
    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/post"
    assert ret.json()["method"] == "POST"
    assert ret.json()["protocol"] == "http"
    assert ret.json()["status"] == {"code": 200, "message": "OK"}

    # request
    assert {"name": "Connection", "value": "keep-alive"} in ret.json()["request"][
        "headers"
    ]
    assert ret.json()["request"]["cookies"] == []
    assert ret.json()["request"]["body"]["filename"] == "upload"
    path_to_content = ret.json()["request"]["body"]["path"]
    assert (
        requests.get(f"http://127.0.0.1:{current_httpdbg_port}/{path_to_content}").text
        == "data to post"
    )

    # response
    assert {"name": "Content-Type", "value": "application/json"} in ret.json()[
        "response"
    ]["headers"]
    assert ret.json()["response"]["cookies"] == []
    assert ret.json()["response"]["body"]["filename"] == "post"
    path_to_content = ret.json()["response"]["body"]["path"]
    assert (
        requests.get(
            f"http://127.0.0.1:{current_httpdbg_port}/{path_to_content}"
        ).status_code
        == 200
    )

    stop_httpdbg()


@pytest.mark.api
@pytest.mark.request
def test_api_get_request_get_status_404(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/0")
    stop_httpdbg()

    assert ret.status_code == 200
    assert ret.json()["url"] == httpbin.url + "/get/abc"
    assert ret.json()["status"] == {"code": 404, "message": "NOT FOUND"}
