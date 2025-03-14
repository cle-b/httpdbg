# -*- coding: utf-8 -*-
import os

import pytest

from httpdbg.mode_module import run_module
from httpdbg.mode_script import run_script
from httpdbg.hooks.all import httprecord


@pytest.mark.unittest
@pytest.mark.group
@pytest.mark.tag
def test_run_module_unittest(httpbin):
    with httprecord() as records:
        os.environ["HTTPDBG_TEST_UNITTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_unittest.py"
        )
        run_module(["unittest", f"{script_to_run}"])

    assert_unittest_records(records)


@pytest.mark.unittest
@pytest.mark.group
@pytest.mark.tag
def test_run_script_unittest(httpbin):
    with httprecord() as records:
        os.environ["HTTPDBG_TEST_UNITTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_unittest.py"
        )
        run_script([f"{script_to_run}"])

    assert_unittest_records(records)


def assert_unittest_records(records):

    assert len(records) == 10
    groups = records.groups

    i_req = 0
    assert records[i_req].url.endswith("/get?setup_module")
    assert groups[records[i_req].group_id].label == "setUpModule (demo_run_unittest)"
    assert (
        "demo_run_unittest.py::setUpModule"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None

    i_req = 1
    assert records[i_req].url.endswith("/get?setup_class")
    assert groups[records[i_req].group_id].label == "TestUnittests::setUpClass"
    assert (
        "demo_run_unittest.py::TestUnittests::setUpClass"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None

    i_req = 2
    assert records[i_req].url.endswith("/get?setup")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case1"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case1"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag == "setUp"

    i_req = 3
    assert records[i_req].url.endswith("/get?testcase1")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case1"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case1"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None

    i_req = 4
    assert records[i_req].url.endswith("/get?teardown")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case1"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case1"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag == "tearDown"

    i_req = 5
    assert records[i_req].url.endswith("/get?setup")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case2"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case2"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag == "setUp"

    i_req = 6
    assert records[i_req].url.endswith("/get?testcase2")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case2"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case2"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None

    i_req = 7
    assert records[i_req].url.endswith("/get?teardown")
    assert groups[records[i_req].group_id].label == "TestUnittests::test_case2"
    assert (
        "demo_run_unittest.py::TestUnittests::test_case2"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag == "tearDown"

    i_req = 8
    assert records[i_req].url.endswith("/get?teardown_class")
    assert groups[records[i_req].group_id].label == "TestUnittests::tearDownClass"
    assert (
        "demo_run_unittest.py::TestUnittests::tearDownClass"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None

    i_req = 9
    assert records[i_req].url.endswith("/get?teardown_module")
    assert groups[records[i_req].group_id].label == "tearDownModule (demo_run_unittest)"
    assert (
        "demo_run_unittest.py::tearDownModule"
        in groups[records[i_req].group_id].full_label
    )
    assert records[i_req].tag is None
