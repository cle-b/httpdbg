# -*- coding: utf-8 -*-
import asyncio
import platform

import pytest
import requests

from httpdbg.hooks.all import httprecord


@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="problem with stack view in windows",
)
@pytest.mark.initiator
def test_initiator_script(httpbin):

    with httprecord() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    initiator = records.initiators[records[0].initiator_id]

    assert initiator.label == 'requests.get(f"{httpbin.url}/get")'

    assert (
        """test_initiator.py", line 19, in test_initiator_script
 19.         requests.get(f"{httpbin.url}/get")
----------
requests.api.get(
    url="""
        + f"{httpbin.url}/get"
        + """
)"""
        in initiator.short_stack
    )

    full_stack_ref = """test_initiator.py", line 19, 
 15. @pytest.mark.initiator
 16. def test_initiator_script(httpbin):
 17. 
 18.     with httprecord() as records:
 19.         requests.get(f"{httpbin.url}/get") <====
 20. 
 21.     assert len(records) == 1
 22.     initiator = records.initiators[records[0].initiator_id]
 23. 
 24.     assert initiator.label == 'requests.get(f"{httpbin.url}/get")'
 25."""  # noqa W291
    full_stack = initiator.stack[0]
    assert (
        full_stack_ref in full_stack
    ), f"--ref--\n{full_stack_ref}\n--new--\n{full_stack}\n"


@pytest.mark.initiator
def test_initiator_same_line_different_initiators(httpbin):
    with httprecord() as records:
        for i in range(2):
            requests.get(f"{httpbin.url}/get")

    assert len(records) == 2

    assert records[0].initiator_id != records[1].initiator_id
    assert (
        records.initiators[records[0].initiator_id]
        == records.initiators[records[1].initiator_id]
    )


@pytest.mark.initiator
def test_initiator_redirection_same_initiator(httpbin):
    with httprecord() as records:
        requests.get(f"{httpbin.url}/redirect-to?url={httpbin.url}/get", verify=False)

    assert len(records) == 2

    assert records[0].initiator_id == records[1].initiator_id


@pytest.mark.initiator
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="problem with stack view in windows",
)
def test_initiator_pytest(httpbin):
    with httprecord() as records:
        requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    initiator = records.initiators[records[0].initiator_id]

    assert initiator.label == 'requests.get(f"{httpbin.url}/get")'
    assert 'requests.get(f"{httpbin.url}/get")' in initiator.short_stack
    assert 'requests.get(f"{httpbin.url}/get") <===' in initiator.stack[0]


@pytest.mark.initiator
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="flaky test on windows",
)
def test_initiator_add_package_fnc(httpbin):
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
        asyncio.run(fnc_async(f"{httpbin.url}/get"))

    # function in a package
    assert (
        records.initiators[records[0].initiator_id].label
        == 'fnc_in_package(f"{httpbin.url}/get")'
    )

    # function in a sub package (no __init__)
    assert (
        records.initiators[records[1].initiator_id].label
        == 'fnc_in_subpackage(f"{httpbin.url}/get")'
    )

    # function in a __init__.py file
    assert (
        records.initiators[records[2].initiator_id].label
        == 'fnc_in_init(f"{httpbin.url}/get")'
    )

    # method
    assert (
        records.initiators[records[3].initiator_id].label
        == 'FakeClient().navigate(f"{httpbin.url}/get")'
    )

    # async function in a package
    assert (
        records.initiators[records[4].initiator_id].label
        == 'asyncio.run(fnc_async(f"{httpbin.url}/get"))'
    )

    with httprecord() as records:
        fnc_in_package(f"{httpbin.url}/get")
        fnc_in_subpackage(f"{httpbin.url}/get")
        fnc_in_init(f"{httpbin.url}/get")
        FakeClient().navigate(f"{httpbin.url}/get")
        asyncio.run(fnc_async(f"{httpbin.url}/get"))

    assert records.initiators[records[0].initiator_id].label == "requests.get(url)"
    assert (
        records.initiators[records[1].initiator_id].label
        == "requests.get(url)  # subpackage"
    )
    assert (
        records.initiators[records[2].initiator_id].label == "requests.get(url)  # init"
    )
    assert (
        records.initiators[records[3].initiator_id].label
        == "requests.get(url)  # method"
    )
    assert records.initiators[records[4].initiator_id].label == "await client.get(url)"
