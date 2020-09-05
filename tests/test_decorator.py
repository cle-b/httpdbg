# -*- coding: utf-8 -*-
import requests

from httpdbg import httpdbg
from httpdbg.webapp import httpdebugk7


def func_do_one_http_request(httpdport):
    requests.get("http://localhost:%d/" % httpdport)


@httpdbg
def func_do_one_http_request_with_decorator(httpdport):
    func_do_one_http_request(httpdport)


def func_do_one_http_request_without_decorator(httpdport):
    func_do_one_http_request(httpdport)


def test_decorator(httpdport):
    assert httpdebugk7["k7"] is None
    func_do_one_http_request_without_decorator(httpdport)
    assert httpdebugk7["k7"] is None
    func_do_one_http_request_with_decorator(httpdport)
    assert len(httpdebugk7["k7"]) == 1
