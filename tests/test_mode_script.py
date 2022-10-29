# -*- coding: utf-8 -*-
import os

import pytest
import requests

from httpdbg.mode_script import run_script
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.server import httpdbg_hook
from httpdbg.server import httpdbg_srv


def test_run_script(httpbin):
    with httpdbg_hook():
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url])


def test_run_script_from_pyhttpdbg_entry_point(httpbin, httpdbg_port, monkeypatch):
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
    )
    monkeypatch.setattr(
        "sys.argv", ["pyhttpdbg", "--script", script_to_run, httpbin.url]
    )

    pyhttpdbg_entry_point(test_mode=True)

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/post"


def test_run_script_with_exception(httpbin, httpdbg_port, capsys):
    with httpdbg_hook():
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_script.py"
        )
        run_script([script_to_run, httpbin.url, "raise_exception"])

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"

    assert "--raise_exception--" in capsys.readouterr().err


def test_run_script_no_args(httpbin, capsys):
    with pytest.raises(SystemExit):
        run_script([])


def test_run_script_not_a_python_script(httpbin, capsys):
    with pytest.raises(SystemExit):
        run_script(["not_a_path_to_a_python_script"])
