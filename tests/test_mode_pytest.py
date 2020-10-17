# -*- coding: utf-8 -*-
import os

import requests

from httpdbg.mode_pytest import run_pytest
from utils import _run_under_httpdbg


def test_run_pytest(httpbin):
    def _test(httpbin):
        os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_pytest(["pytest", script_to_run, "-k", "test_demo"])

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 3
    assert reqs[0]["uri"] == httpbin.url + "/post"
    assert reqs[1]["uri"] == httpbin.url + "/get"
    assert reqs[2]["uri"] == httpbin.url + "/put"
