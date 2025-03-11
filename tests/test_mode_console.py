# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.mode_console import run_console, console_exit
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.hooks.all import httprecord
from httpdbg.server import httpdbg_srv


def test_console_exit():
    with pytest.raises(SystemExit):
        console_exit()


def test_run_console_from_pyhttpdbg_entry_point(
    httpbin, httpdbg_port, monkeypatch, capsys
):
    monkeypatch.setattr("sys.argv", ["pyhttpdb", "--console"])

    pyhttpdbg_entry_point(test_mode=True)

    assert "test_mode is on" in capsys.readouterr().out


def test_run_console_from_pyhttpdbg_entry_point_default(
    httpbin, httpdbg_port, monkeypatch, capsys
):
    monkeypatch.setattr("sys.argv", ["pyhttpdb"])

    pyhttpdbg_entry_point(test_mode=True)

    assert "test_mode is on" in capsys.readouterr().out


def test_run_console(httpbin, httpdbg_host, httpdbg_port):
    with httpdbg_srv(httpdbg_host, httpdbg_port) as records:
        with httprecord(records):
            new_console = run_console(records, test_mode=True)
            new_console.push("import requests")
            new_console.push(f"requests.get('{httpbin.url}/get')")
            with pytest.raises(SystemExit):
                new_console.push("exit()")

        ret = requests.get(f"http://{httpdbg_host}:{httpdbg_port}/requests")

        reqs = ret.json()["requests"]

    assert len(reqs) == 1
    assert reqs[list(reqs.keys())[0]]["url"] == httpbin.url + "/get"


@pytest.mark.group
def test_run_console_group(httpbin):

    with httprecord() as records:
        new_console = run_console(records, test_mode=True)
        new_console.push("import requests")
        new_console.push(f"requests.get('{httpbin.url}/get')")
        new_console.push("if True:")
        new_console.push(f"    requests.post('{httpbin.url}/post')")
        new_console.push("")
        with pytest.raises(SystemExit):
            new_console.push("exit()")

    assert len(records) == 2
    assert (
        records.groups[records[0].group_id].label
        == f"requests.get('{httpbin.url}/get')"
    )
    assert records.groups[records[0].group_id].full_label.endswith(
        f">>> requests.get('{httpbin.url}/get') <===="
    )

    assert records.groups[records[1].group_id].label == "(block)"
    assert records.groups[records[1].group_id].full_label.endswith(
        f">>> if True:\n              requests.post('{httpbin.url}/post')"
    )
