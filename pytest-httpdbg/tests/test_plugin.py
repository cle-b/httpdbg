# -*- coding: utf-8 -*-
import glob
import os

confest_py = """
        import pytest
        import requests
        from pytest_httpdbg import httpdbg_record_filename

        @pytest.fixture(scope="session")
        def fixture_session(httpbin):
            requests.get(httpbin.url + "/setupsession")
            yield
            requests.get(httpbin.url + "/teardownsession")


        @pytest.fixture()
        def fixture_function(httpbin, fixture_session):
            requests.get(httpbin.url + "/setupfunction")
            yield
            requests.get(httpbin.url + "/teardownfunction")



    """


def test_no_httpdbg(pytester):
    pytester.makeconftest(confest_py)

    pytester.makepyfile(
        """
        import requests

        def test_get(httpbin, fixture_session, fixture_function):
            requests.get(httpbin.url + "/intest")

        def test_post(httpbin, fixture_session):
            requests.post(httpbin.url + "/intest")
    """
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=2)


def test_record_in_dir(pytester, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    pytester.makeconftest(confest_py)

    pytester.makepyfile(
        """
        import requests

        def test_get(httpbin, fixture_session, fixture_function):
            requests.get(httpbin.url + "/intest")

        def test_post(httpbin, fixture_session):
            requests.post(httpbin.url + "/intest")
    """
    )

    result = pytester.runpytest("--httpdbg", "--httpdbg-dir", str(logs_dir))

    result.assert_outcomes(passed=2)

    assert len(list(logs_dir.iterdir())) == 2

    filename = glob.glob(f"{logs_dir}/*test_get*")[0]
    with open(os.path.join(logs_dir, filename), "r") as f:
        log = f.read()

    assert "test_get" in log
    assert "test_post" not in log


def test_with_initiator(pytester, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    pytester.makefile(
        ".py", fakepackage="import requests\ndef coucou(url):\n    requests.get(url)\n"
    )

    pytester.makepyfile(
        """
        import fakepackage

        def test_with_initiator_fake(httpbin):
            fakepackage.coucou(httpbin.url)
    """
    )

    result = pytester.runpytest(
        "--httpdbg",
        "--httpdbg-dir",
        str(logs_dir),
        "--httpdbg-initiator",
        "fakepackage",
    )

    result.assert_outcomes(passed=1)

    assert len(list(logs_dir.iterdir())) == 1

    filename = glob.glob(f"{logs_dir}/*test_with_initiator_fake*")[0]
    with open(os.path.join(logs_dir, filename), "r") as f:
        log = f.read()

    assert "test_with_initiator.py::test_with_initiator_fake" in log
    assert "requests.get" not in log
    assert "coucou(" in log


def test_without_initiator(pytester, tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    pytester.makefile(
        ".py", fakepackage="import requests\ndef coucou(url):\n    requests.get(url)\n"
    )

    pytester.makepyfile(
        """
        import fakepackage

        def test_without_initiator_fake(httpbin):
            fakepackage.coucou(httpbin.url)
    """
    )

    result = pytester.runpytest("--httpdbg", "--httpdbg-dir", str(logs_dir))

    result.assert_outcomes(passed=1)

    assert len(list(logs_dir.iterdir())) == 1

    filename = glob.glob(f"{logs_dir}/*test_without_initiator_fake*")[0]
    with open(os.path.join(logs_dir, filename), "r") as f:
        log = f.read()

    assert "test_without_initiator.py::test_without_initiator_fake" in log
    assert "requests.get" in log
    assert "coucou(" not in log
