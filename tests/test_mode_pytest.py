# -*- coding: utf-8 -*-
import io
import os

import requests

from httpdbg.httpdbg import ServerThread, app
from httpdbg.mode_pytest import run_pytest
from httpdbg.__main__ import pyhttpdbg_entry_point
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


def test_run_pytest_from_pyhttpdbg_entry_point(httpbin, monkeypatch):
    os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
    )

    monkeypatch.setattr(
        "sys.argv", ["pyhttpdb", "pytest", script_to_run, "-k", "test_demo"]
    )
    # to terminate the httpdbg server
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    pyhttpdbg_entry_point()

    # we need to restart a new httpdbg server as the previous has been stopped
    server = ServerThread(6000, app)
    server.start()

    ret = requests.get("http://127.0.0.1:6000/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 3
    assert reqs[0]["uri"] == httpbin.url + "/post"
    assert reqs[1]["uri"] == httpbin.url + "/get"
    assert reqs[2]["uri"] == httpbin.url + "/put"

    server.shutdown()


def test_run_pytest_with_exception(capsys):
    def _test():
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_pytest(["pytest", script_to_run, "-k", "test_demo_raise_exception"])

    stop_httpdbg, current_httpdbg_port = _run_under_httpdbg(_test)

    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")
    stop_httpdbg()

    reqs = ret.json()["requests"]

    assert len(reqs) == 0

    assert "fixture_which_do_not_exists" in capsys.readouterr().out
