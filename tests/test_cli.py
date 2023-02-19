# -*- coding: utf-8 -*-
import pkg_resources
import pytest

from httpdbg.__main__ import pyhttpdbg_entry_point


@pytest.mark.cli
def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyhttpdb", "--version"])

    pyhttpdbg_entry_point(test_mode=True)

    assert (
        pkg_resources.get_distribution("httpdbg").version
        in capsys.readouterr().out.strip()
    )
