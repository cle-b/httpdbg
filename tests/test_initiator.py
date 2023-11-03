# -*- coding: utf-8 -*-
import asyncio
import platform
import sys

import pytest
import requests

from httpdbg.hooks.all import httprecord


@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="problem with stack view in windows",
)
@pytest.mark.initiator
def test_initiator_script(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httprecord() as records:
            requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    assert http_record.initiator.short_label == 'requests.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None

    assert (
        """test_initiator.py", line 21, in test_initiator_script
 21.             requests.get(f"{httpbin.url}/get")
----------
requests.api.get(
    url="""
        + f"{httpbin.url}/get"
        + """
)"""
        in http_record.initiator.short_stack
    )

    assert (
        """test_initiator.py", line 21, 
 17. def test_initiator_script(httpbin, monkeypatch):
 18.     with monkeypatch.context() as m:
 19.         m.delenv("PYTEST_CURRENT_TEST")
 20.         with httprecord() as records:
 21.             requests.get(f"{httpbin.url}/get") <====
 22. 
 23.     assert len(records) == 1
 24.     http_record = records[0]
 25. 
 26.     assert http_record.initiator.short_label == \'requests.get(f"{httpbin.url}/get")\'
 27.     assert http_record.initiator.long_label is None
 28."""  # noqa W291
        in http_record.initiator.stack[0]
    )


@pytest.mark.initiator
def test_initiator_same_line_different_initiators(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httprecord() as records:
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
        with httprecord() as records:
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
    with httprecord() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1

    assert records[0].initiator.short_label == "test_initiator_pytest"
    assert (
        records[0].initiator.long_label
        == "tests/test_initiator.py::test_initiator_pytest"
    )
    assert 'requests.get(f"{httpbin.url}/get")' in records[0].initiator.short_stack
    assert 'requests.get(f"{httpbin.url}/get") <===' in records[0].initiator.stack[0]


@pytest.mark.initiator
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="flaky test on windows",
)
def test_initiator_add_package_fnc(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")

        # all cases must be tested in the same test
        with httprecord(initiators=["initiator_pck"]) as records:
            from initiator_pck.initiator2.mod2 import fnc_in_subpackage
            from initiator_pck.mod1 import fnc_in_package
            from initiator_pck import fnc_async
            from initiator_pck.initiator2.initiator3 import fnc_in_init
            from initiator_pck.initiator2.mod2 import FakeClient

            fnc_in_package(f"{httpbin.url}/get")
            fnc_in_subpackage(f"{httpbin.url}/get")
            fnc_in_init(f"{httpbin.url}/get")
            FakeClient().navigate(f"{httpbin.url}/get")
            if sys.version_info >= (3, 7):
                asyncio.run(fnc_async(f"{httpbin.url}/get"))

        # function in a package
        assert (
            records[0].initiator.short_label == 'fnc_in_package(f"{httpbin.url}/get")'
        )

        # function in a sub package (no __init__)
        assert (
            records[1].initiator.short_label
            == 'fnc_in_subpackage(f"{httpbin.url}/get")'
        )

        # function in a __init__.py file
        assert records[2].initiator.short_label == 'fnc_in_init(f"{httpbin.url}/get")'

        # method
        assert (
            records[3].initiator.short_label
            == 'FakeClient().navigate(f"{httpbin.url}/get")'
        )

        # async function in a package
        if sys.version_info >= (3, 7):
            assert (
                records[4].initiator.short_label
                == 'asyncio.run(fnc_async(f"{httpbin.url}/get"))'
            )

        with httprecord() as records:
            fnc_in_package(f"{httpbin.url}/get")
            fnc_in_subpackage(f"{httpbin.url}/get")
            fnc_in_init(f"{httpbin.url}/get")
            FakeClient().navigate(f"{httpbin.url}/get")
            if sys.version_info >= (3, 7):
                asyncio.run(fnc_async(f"{httpbin.url}/get"))

        assert records[0].initiator.short_label == "requests.get(url)"
        assert records[1].initiator.short_label == "requests.get(url)  # subpackage"
        assert records[2].initiator.short_label == "requests.get(url)  # init"
        assert records[3].initiator.short_label == "requests.get(url)  # method"
        if sys.version_info >= (3, 7):
            assert records[4].initiator.short_label == "await client.get(url)"
