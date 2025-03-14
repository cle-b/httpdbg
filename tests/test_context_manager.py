# -*- coding: utf-8 -*-
from httpdbg import httprecord

import pytest
import requests


@pytest.mark.cm
@pytest.mark.api
def test_context_manager(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1


@pytest.mark.cm
@pytest.mark.api
def test_context_manager_two_calls(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records:
        requests.get(httpbin.url + "/get")

    assert len(records.requests) == 1
    for _, req in records.requests.items():
        assert req.method.lower() == "get"

    with httprecord() as records2:
        requests.post(httpbin.url + "/post")

    assert len(records2.requests) == 1
    for _, req in records2.requests.items():
        assert req.method.lower() == "post"


@pytest.mark.cm
def test_context_manager_reentrant(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records1:
        requests.get(httpbin.url + "/get/a1")
        with httprecord() as records2:
            requests.get(httpbin.url + "/get/b1")
            requests.get(httpbin.url + "/get/b2")
            with httprecord() as records3:
                requests.get(httpbin.url + "/get/c1")
        requests.get(httpbin.url + "/get/a2")

    requests.get(httpbin.url + "/get")

    assert len(records1.requests) == 5
    assert len(records2.requests) == 3
    assert len(records3.requests) == 1


@pytest.mark.cm
@pytest.mark.initiator
def test_context_manager_reentrant_initiator(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records1:
        requests.get(httpbin.url + "/get/a1")
        with httprecord() as records2:
            requests.get(httpbin.url + "/get/b1")
            requests.get(httpbin.url + "/get/b2")
            with httprecord() as records3:
                requests.get(httpbin.url + "/get/c1")
        requests.get(httpbin.url + "/get/a2")

    requests.get(httpbin.url + "/get")

    assert (
        records1.initiators[records1[0].initiator_id].label
        == 'requests.get(httpbin.url + "/get/a1")'
    )
    assert (
        records1.initiators[records1[1].initiator_id].label
        == 'requests.get(httpbin.url + "/get/b1")'
    )
    assert (
        records1.initiators[records1[2].initiator_id].label
        == 'requests.get(httpbin.url + "/get/b2")'
    )
    assert (
        records1.initiators[records1[3].initiator_id].label
        == 'requests.get(httpbin.url + "/get/c1")'
    )
    assert (
        records1.initiators[records1[4].initiator_id].label
        == 'requests.get(httpbin.url + "/get/a2")'
    )
    assert (
        records2.initiators[records2[0].initiator_id].label
        == 'requests.get(httpbin.url + "/get/b1")'
    )
    assert (
        records2.initiators[records2[1].initiator_id].label
        == 'requests.get(httpbin.url + "/get/b2")'
    )
    assert (
        records2.initiators[records2[2].initiator_id].label
        == 'requests.get(httpbin.url + "/get/c1")'
    )
    assert (
        records3.initiators[records3[0].initiator_id].label
        == 'requests.get(httpbin.url + "/get/c1")'
    )


@pytest.mark.cm
@pytest.mark.group
def test_context_manager_reentrant_group(httpbin):
    requests.get(httpbin.url + "/get")

    with httprecord() as records1:
        requests.get(httpbin.url + "/get?a1")
        with httprecord() as records2:
            requests.get(httpbin.url + "/get?b1")
            requests.get(httpbin.url + "/get?b2")
            with httprecord() as records3:
                requests.get(httpbin.url + "/get?c1")
        requests.get(httpbin.url + "/get?a2")

    requests.get(httpbin.url + "/get")

    assert (
        records1.groups[records1[0].group_id].label
        == 'requests.get(httpbin.url + "/get?a1")'
    )
    assert (
        records1.groups[records1[1].group_id].label
        == 'requests.get(httpbin.url + "/get?b1")'
    )
    assert (
        records1.groups[records1[2].group_id].label
        == 'requests.get(httpbin.url + "/get?b2")'
    )
    assert (
        records1.groups[records1[3].group_id].label
        == 'requests.get(httpbin.url + "/get?c1")'
    )
    assert (
        records1.groups[records1[4].group_id].label
        == 'requests.get(httpbin.url + "/get?a2")'
    )
    assert (
        records2.groups[records2[0].group_id].label
        == 'requests.get(httpbin.url + "/get?b1")'
    )
    assert (
        records2.groups[records2[1].group_id].label
        == 'requests.get(httpbin.url + "/get?b2")'
    )
    assert (
        records2.groups[records2[2].group_id].label
        == 'requests.get(httpbin.url + "/get?c1")'
    )
    assert (
        records3.groups[records3[0].group_id].label
        == 'requests.get(httpbin.url + "/get?c1")'
    )
