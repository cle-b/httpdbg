# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.mode_console import run_console, console_exit
from utils import _run_under_httpdbg


def test_console_exit():
    with pytest.raises(SystemExit):
        console_exit()


def test_run_console(httpbin):
    def _test(httpbin):
        new_console = run_console(test_mode=True)
        new_console.push("import requests")
        new_console.push(f"requests.get('{httpbin.url}/get')")
        with pytest.raises(SystemExit):
            new_console.push("exit()")

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[0]["uri"] == httpbin.url + "/get"
