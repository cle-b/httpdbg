# -*- coding: utf-8 -*-
import io
import os

import requests

from httpdbg.httpdbg import ServerThread, app
from httpdbg.mode_script import run_script
from httpdbg.__main__ import pyhttpdbg_entry_point
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


def test_run_script_from_pyhttpdbg_entry_point(httpbin, monkeypatch):
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
    )
    monkeypatch.setattr("sys.argv", ["pyhttpdbg", script_to_run, httpbin.url])
    # to terminate the httpdbg server
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    pyhttpdbg_entry_point()

    # we need to restart a new httpdbg server as the previous has been stopped
    server = ServerThread(6000, app)
    server.start()

    ret = requests.get("http://127.0.0.1:6000/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[0]["uri"] == httpbin.url + "/get"
    assert reqs[1]["uri"] == httpbin.url + "/post"

    server.shutdown()


def test_run_script_with_exception(httpbin, capsys):
    def _test(httpbin):
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url, "raise_exception"])

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test, httpbin)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[0]["uri"] == httpbin.url + "/get"

    assert "--raise_exception--" in capsys.readouterr().err
