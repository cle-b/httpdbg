# -*- coding: utf-8 -*-
import requests

from utils import _run_under_httpdbg


def test_api_requests_one_request(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get("http://127.0.0.1:%d/requests" % current_httpdbg_port)
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[0]["uri"] == httpbin.url + "/get"


def test_api_requests_two_requests(httpbin):
    def _test(httpbin):
        requests.get(httpbin.url + "/get/abc")
        requests.get(httpbin.url + "/get/def")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get("http://127.0.0.1:%d/requests" % current_httpdbg_port)
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[0]["uri"] == httpbin.url + "/get/abc"
    assert reqs[1]["uri"] == httpbin.url + "/get/def"
