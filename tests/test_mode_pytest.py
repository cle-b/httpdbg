# -*- coding: utf-8 -*-
import os

import pytest
import requests

from httpdbg.mode_pytest import run_pytest
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.server import httpdbg_hook
from httpdbg.server import httpdbg_srv


@pytest.mark.pytest
def test_run_pytest(httpbin):
    with httpdbg_hook():
        os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_pytest([f"{script_to_run}::test_demo_pytest"])


@pytest.mark.pytest
def test_run_pytest_from_pyhttpdbg_entry_point(httpbin, httpdbg_port, monkeypatch):
    os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
    )

    monkeypatch.setattr(
        "sys.argv", ["pyhttpdbg", "--pytest", f"{script_to_run}::test_demo_pytest"]
    )

    pyhttpdbg_entry_point(test_mode=True)

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 3
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/post"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[2]]["url"] == httpbin.url + "/put"


@pytest.mark.pytest
def test_run_pytest_with_exception(httpdbg_port, capsys):
    with httpdbg_hook():
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_pytest([f"{script_to_run}::test_demo_raise_exception"])

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 0

    assert "fixture_which_does_not_exist" in capsys.readouterr().out


@pytest.mark.api
@pytest.mark.request
@pytest.mark.pytest
def test_run_pytest_initiator(httpbin, httpdbg_port):
    with httpdbg_hook():
        os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_pytest([f"{script_to_run}::test_demo_pytest"])

    with httpdbg_srv(httpdbg_port):
        ret = requests.get(f"http://127.0.0.1:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert (
        reqs[list(reqs.keys())[0]]["initiator"].get("short_label") == "test_demo_pytest"
    )
    assert (
        reqs[list(reqs.keys())[0]]["initiator"].get("long_label")
        == "tests/demo_run_pytest.py::test_demo_pytest"
    )

    assert len(reqs) == 3
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/post"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[2]]["url"] == httpbin.url + "/put"
