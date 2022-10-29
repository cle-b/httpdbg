# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.mode_console import run_console, console_exit
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.server import httpdbg_hook
from httpdbg.server import httpdbg_srv


def test_console_exit():
    with pytest.raises(SystemExit):
        console_exit()


def test_run_console(httpbin, httpdbg_port):
    with httpdbg_hook():
        new_console = run_console(test_mode=True)
        new_console.push("import requests")
        new_console.push(f"requests.get('{httpbin.url}/get')")
        with pytest.raises(SystemExit):
            new_console.push("exit()")

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

        reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"


def test_run_console_from_pyhttpdbg_entry_point(
    httpbin, httpdbg_port, monkeypatch, capsys
):
    monkeypatch.setattr("sys.argv", ["pyhttpdb"])

    pyhttpdbg_entry_point(test_mode=True)

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

        reqs = ret.json()["requests"]

    assert len(reqs) == 0

    assert "test_mode is on" in capsys.readouterr().out
