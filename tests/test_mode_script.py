# -*- coding: utf-8 -*-
import os

import requests

from httpdbg.mode_script import run_script
from utils import _run_under_httpdbg


def test_run_script(httpbin):
    def _test(httpbin):
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url])

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[0]["uri"] == httpbin.url + "/get"
    assert reqs[1]["uri"] == httpbin.url + "/post"
