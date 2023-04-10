# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.hooks.all import httpdbg


@pytest.mark.initiator
def test__initiator_script(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            requests.get(f"{httpbin.url}/get")

    assert len(records) == 1
    http_record = records[0]

    print(http_record.initiator.stack)
    assert http_record.initiator.short_label == 'requests.get(f"{httpbin.url}/get")'
    assert http_record.initiator.long_label is None
    assert (
        http_record.initiator.short_stack
        == """File "/home/cle/dev/httpdbg/tests/test_initiator.py", line 13, in test__initiator_script
 13.             requests.get(f"{httpbin.url}/get")
----------
requests.api.get(
    url="""
        + f"{httpbin.url}/get"
        + """
)"""
    )
    assert http_record.initiator.stack == [
        """File "/home/cle/dev/httpdbg/tests/test_initiator.py", line 13, 
 9. def test__initiator_script(httpbin, monkeypatch):
 10.     with monkeypatch.context() as m:
 11.         m.delenv("PYTEST_CURRENT_TEST")
 12.         with httpdbg() as records:
 13.             requests.get(f"{httpbin.url}/get") <====
 14. 
 15.     assert len(records) == 1
 16.     http_record = records[0]
 17. 
 18.     print(http_record.initiator.stack)
 19.     assert http_record.initiator.short_label == \'requests.get(f"{httpbin.url}/get")\'
 20.     assert http_record.initiator.long_label is None
"""  # noqa W291
    ]


@pytest.mark.initiator
def test__initiator_same_line_different_initiators(httpbin, monkeypatch):
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
def test__initiator_redirection_same_initiator(httpbin, monkeypatch):
    with monkeypatch.context() as m:
        m.delenv("PYTEST_CURRENT_TEST")
        with httpdbg() as records:
            requests.get(
                f"{httpbin.url}/redirect-to?url={httpbin.url}/get", verify=False
            )

    assert len(records) == 2

    assert records[0].initiator is records[1].initiator
