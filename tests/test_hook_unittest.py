# -*- coding: utf-8 -*-
import os

import pytest

from httpdbg.mode_module import run_module
from httpdbg.hooks.all import httprecord


@pytest.mark.unittest
@pytest.mark.group
@pytest.mark.tag
def test_run_unittest(httpbin):
    with httprecord() as records:
        os.environ["HTTPDBG_TEST_UNITTEST_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_unittest.py"
        )
        run_module(["unittest", f"{script_to_run}"])

    assert len(records) == 8
    groups = records.groups

    assert records[0].url.endswith("/setup_class")
    assert groups[records[0].group_id].label == "TestUnittests::setUpClass"
    assert "demo_run_unittest.py::TestUnittests::setUpClass" in groups[records[0].group_id].full_label
    assert records[0].tag is None

    assert records[1].url.endswith("/setup")
    assert groups[records[1].group_id].label == "TestUnittests::test_case1"
    assert "demo_run_unittest.py::TestUnittests::test_case1" in groups[records[1].group_id].full_label
    assert records[1].tag == "setUp"

    assert records[2].url.endswith("/testcase1")
    assert groups[records[2].group_id].label == "TestUnittests::test_case1"
    assert "demo_run_unittest.py::TestUnittests::test_case1" in groups[records[2].group_id].full_label
    assert records[2].tag is None

    assert records[3].url.endswith("/teardown")
    assert groups[records[3].group_id].label == "TestUnittests::test_case1"
    assert "demo_run_unittest.py::TestUnittests::test_case1" in groups[records[3].group_id].full_label
    assert records[3].tag == "tearDown"

    assert records[4].url.endswith("/setup")
    assert groups[records[4].group_id].label == "TestUnittests::test_case2"
    assert "demo_run_unittest.py::TestUnittests::test_case2" in groups[records[4].group_id].full_label
    assert records[4].tag == "setUp"

    assert records[5].url.endswith("/testcase2")
    assert groups[records[5].group_id].label == "TestUnittests::test_case2"
    assert "demo_run_unittest.py::TestUnittests::test_case2" in groups[records[5].group_id].full_label
    assert records[5].tag is None

    assert records[6].url.endswith("/teardown")
    assert groups[records[6].group_id].label == "TestUnittests::test_case2"
    assert "demo_run_unittest.py::TestUnittests::test_case2" in groups[records[6].group_id].full_label
    assert records[6].tag == "tearDown"

    assert records[7].url.endswith("/teardown_class")
    assert groups[records[7].group_id].label == "TestUnittests::tearDownClass"
    assert "demo_run_unittest.py::TestUnittests::tearDownClass" in groups[records[7].group_id].full_label
    assert records[7].tag is None
