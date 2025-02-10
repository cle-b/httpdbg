import os
import platform

import pytest

from httpdbg import httprecord
from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.mode_script import run_script


@pytest.mark.script
def test_run_script_multithread(httpbin):

    if HTTPDBG_MULTIPROCESS_DIR in os.environ:
        del os.environ[HTTPDBG_MULTIPROCESS_DIR]

    with httprecord() as records:
        os.environ["HTTPDBG_TEST_MULTITHREAD_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_multithread.py"
        )
        run_script([script_to_run, httpbin.url])

    assert len(records) == 3
    pids = []
    for record in records:
        pids.append(record.url.split("/")[-1])
    assert len(set(pids)) == 1


@pytest.mark.script
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="the test fails on the CI but the feature works on windows",
)
def test_run_script_multiprocess(httpbin):

    if HTTPDBG_MULTIPROCESS_DIR in os.environ:
        del os.environ[HTTPDBG_MULTIPROCESS_DIR]

    with httprecord() as records:
        os.environ["HTTPDBG_TEST_MULTIPROCESS_BASE_URL"] = httpbin.url
        script_to_run = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "demo_run_multiprocess.py"
        )
        run_script([script_to_run, httpbin.url])

    assert len(records) == 3
    pids = []
    for record in records:
        pids.append(record.url.split("/")[-1])
    assert len(set(pids)) == 3
