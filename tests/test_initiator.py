# -*- coding: utf-8 -*-
import platform

import pytest
import requests

from httpdbg.hooks.all import httpdbg


@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="problem with stack view in windows",
)
@pytest.mark.initiator
def test_initiator_script(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == 'requests.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None

    assert (
        """test_initiator.py", line 19, in test_initiator_script
 19.             requests.get(f"{httpbin.url}/get")
----------
requests.api.get(
    url="""
        + f"{httpbin.url}/get"
        + """
)"""
        in http_record.initiator.short_stack
    )

    assert (
        """test_initiator.py", line 19, 
 15. def test_initiator_script(httpbin, monkeypatch):
 16.     with monkeypatch.context() as m:
 17.         m.delenv("PYTEST_CURRENT_TEST")
 18.         with httpdbg() as records:
 19.             requests.get(f"{httpbin.url}/get") <====
 20. 
 21.     assert len(records) == 1
 22.     http_record = records[0]
 23. 
 24.     assert http_record.initiator.short_label == \'requests.get(f"{httpbin.url}/get")\'
 25.     assert http_record.initiator.long_label is None
 26."""  # noqa W291
        in http_record.initiator.stack[0]
    )


@pytest.mark.initiator
def test_initiator_same_line_different_initiators(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            for i in range(2):
                requests.get(f"{httpbin.url}/get")

    assert len(records) == 2

    assert records[0].initiator is not records[1].initiator
    assert records[0].initiator.id != records[1].initiator.id
    assert records[0].initiator == records[1].initiator


@pytest.mark.initiator
def test_initiator_redirection_same_initiator(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            requests.get(
                f"{httpbin.url}/redirect-to?url={httpbin.url}/get", verify=False
            )

    assert len(records) == 2

    assert records[0].initiator is records[1].initiator


@pytest.mark.initiator
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="problem with stack view in windows",
)
def test_initiator_pytest(httpbin):
    with httpdbg() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1

    assert records[0].initiator.short_label == "test_initiator_pytest"
    assert (
        records[0].initiator.long_label
        == "tests/test_initiator.py::test_initiator_pytest"
    )
    assert 'requests.get(f"{httpbin.url}/get")' in records[0].initiator.short_stack
    assert 'requests.get(f"{httpbin.url}/get") <===' in records[0].initiator.stack[0]
