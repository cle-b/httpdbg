# -*- coding: utf-8 -*-
import os

import pytest

from httpdbg.mode_module import run_module
from httpdbg.hooks.all import httprecord


@pytest.mark.pytest
@pytest.mark.group
@pytest.mark.tag
def test_run_pytest_tag(httpbin):
    with httprecord() as records:
        os.environ["HTTPDBG_TEST_PYTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_pytest.py"
        )
        run_module(["pytest", f"{script_to_run}::test_demo_pytest_fixture_tag"])

    assert len(records) == 2
    groups = records.groups

    assert records[0].url.endswith("/post")
    assert groups[records[0].group_id].label == "test_demo_pytest_fixture_tag"
    assert (
        "demo_run_pytest.py::test_demo_pytest_fixture_tag"
        in groups[records[0].group_id].full_label
    )
    assert records[0].tag == "my_fixture"

    assert records[1].url.endswith("/get")
    assert groups[records[1].group_id].label == "test_demo_pytest_fixture_tag"
    assert (
        "demo_run_pytest.py::test_demo_pytest_fixture_tag"
        in groups[records[1].group_id].full_label
    )
    assert records[1].tag is None
