# -*- coding: utf-8 -*-
import pytest

from httpdbg import VERSION
from httpdbg.__main__ import pyhttpdbg_entry_point


@pytest.mark.cli
def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyhttpdb", "--version"])

    pyhttpdbg_entry_point(test_mode=True)

    assert VERSION in capsys.readouterr().out.strip()
