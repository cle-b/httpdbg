# -*- coding: utf-8 -*-
import io
import os

import pytest
import requests

from httpdbg.mode_script import run_script
from httpdbg.__main__ import pyhttpdbg_entry_point
from utils import _run_under_httpdbg
from utils import _run_httpdbg_server


def test_run_script(httpbin):
    def _test(httpbin):
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url])

    _run_under_httpdbg(_test, httpbin)


def test_run_script_from_pyhttpdbg_entry_point(httpbin, monkeypatch):
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
    )
    monkeypatch.setattr(
        "sys.argv", ["pyhttpdbg", "--script", script_to_run, httpbin.url]
    )
    # to terminate the httpdbg server
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    pyhttpdbg_entry_point()

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/post"

    server.shutdown()


def test_run_script_with_exception(httpbin, capsys):
    def _test(httpbin):
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url, "raise_exception"])

    _run_under_httpdbg(_test, httpbin)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = _run_httpdbg_server()

    ret = requests.get(f"http://127.0.0.1:{server.port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"

    assert "--raise_exception--" in capsys.readouterr().err

    server.shutdown()


def test_run_script_no_args(httpbin, capsys):
    with pytest.raises(SystemExit):
        run_script([])


def test_run_script_not_a_python_script(httpbin, capsys):
    with pytest.raises(SystemExit):
        run_script(["not_a_path_to_a_python_script"])
