# -*- coding: utf-8 -*-
import os

import pytest
import requests

from httpdbg.mode_module import run_module
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.hooks.all import httprecord
from httpdbg.server import httpdbg_srv


@pytest.mark.pytest
def test_run_pytest_from_pyhttpdbg_entry_point(httpbin, monkeypatch):
    os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
    script_to_run = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
    )

    monkeypatch.setattr(
        "sys.argv",
        ["pyhttpdbg", "--module", "pytest", f"{script_to_run}::test_demo_pytest"],
    )

    pyhttpdbg_entry_point(test_mode=True)

    # this is not easy to verify here if the HTTP requests have been recorded,
    # but we verify that in the test below


@pytest.mark.pytest
def test_run_pytest(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
            script_to_run = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
            )
            run_module(["pytest", f"{script_to_run}::test_demo_pytest"])

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 3
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/post"
    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[2]]["url"] == httpbin.url + "/put"


@pytest.mark.pytest
def test_run_pytest_with_exception(httpdbg_host, httpdbg_port, capsys):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            script_to_run = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
            )
            run_module(["pytest", f"{script_to_run}::test_demo_raise_exception"])

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 0

    assert "fixture_which_does_not_exist" in capsys.readouterr().out


@pytest.mark.api
@pytest.mark.pytest
@pytest.mark.initiator
def test_run_pytest_initiator(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
            script_to_run = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
            )
            run_module(["pytest", f"{script_to_run}::test_demo_pytest"])

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]
    initiatiors = ret.json()["initiators"]
    initiator = initiatiors[reqs[list(reqs.keys())[0]]["initiator_id"]]

    assert initiator.get("label") == 'requests.post(f"{base_url}/post")'

    assert (
        reqs[list(reqs.keys())[0]]["initiator_id"]
        != reqs[list(reqs.keys())[1]]["initiator_id"]
    )


@pytest.mark.api
@pytest.mark.pytest
@pytest.mark.group
def test_run_pytest_group(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
            script_to_run = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
            )
            run_module(["pytest", f"{script_to_run}::test_demo_pytest"])

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]
    groups = ret.json()["groups"]
    group = groups[reqs[list(reqs.keys())[0]]["group_id"]]

    assert group["label"] == "test_demo_pytest"
    assert group["full_label"] == "tests/demo_run_pytest.py::test_demo_pytest"


@pytest.mark.api
@pytest.mark.pytest
@pytest.mark.tag
def test_run_pytest_tag(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
            script_to_run = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
            )
            run_module(["pytest", f"{script_to_run}::test_demo_pytest_fixture_tag"])

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    assert len(reqs) == 2

    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/post"
    assert reqs[list(reqs.keys())[0]]["tag"] == "my_fixture"

    assert reqs[list(reqs.keys())[1]]["url"] == httpbin.url + "/get"
    assert reqs[list(reqs.keys())[1]]["tag"] is None
