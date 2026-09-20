import pytest

from httpdbg import __version__
from httpdbg.__main__ import pyhttpdbg_entry_point
from httpdbg.args import read_args


@pytest.mark.cli
def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyhttpdb", "--version"])

    pyhttpdbg_entry_point(test_mode=True)

    assert __version__ in capsys.readouterr().out.strip()


@pytest.mark.cli
def test_read_args_split_httpdbg_and_script_args():
    """Split httpdbg arguments from the arguments passed to the script/module."""
    httpdbg_args_parsed, client_args = read_args(
        ["--port", "345", "--script", "demo.py", "--script", "xyz"]
    )
    assert httpdbg_args_parsed.port == 345
    assert httpdbg_args_parsed.script == "demo.py"
    assert client_args == ["demo.py", "--script", "xyz"]


@pytest.mark.cli
def test_read_args_split_httpdbg_and_script_args_same_args():
    """Allow script/module arguments to reuse httpdbg command-line same options."""
    read_args(["--script", "demo.py", "--script", "xyz"])
    read_args(["--script", "demo.py", "-m", "xyz"])
