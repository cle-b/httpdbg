# -*- coding: utf-8 -*-
import io

import pytest
import requests

from httpdbg.httpdbg import ServerThread, app
from httpdbg.mode_console import run_console, console_exit
from httpdbg.__main__ import pyhttpdbg_entry_point
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
    assert reqs[0]["url"] == httpbin.url + "/get"


def test_run_console_from_pyhttpdbg_entry_point(httpbin, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyhttpdb"])
    # to terminate the httpdbg server
    monkeypatch.setattr("sys.stdin", io.StringIO("\n"))
    pyhttpdbg_entry_point(test_mode=True)

    # we need to restart a new httpdbg server as the previous has been stopped
    server = ServerThread(6000, app)
    server.start()

    ret = requests.get("http://127.0.0.1:6000/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 0

    server.shutdown()

    assert "test_mode is on" in capsys.readouterr().out
