# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
from typing import List, Tuple

from httpdbg.log import LogLevel


def read_args(args: List[str]) -> Tuple[argparse.Namespace, List[str]]:
    httpdbg_args = args
    client_args = []
    for action in ["--console", "--module", "-m", "--script"]:
        if action in args:
            httpdbg_args = args[: args.index(action) + 2]
            client_args = args[args.index(action) + 1 :]
            break

    parser = argparse.ArgumentParser(
        description="httdbg - a very simple tool to debug HTTP(S) client requests"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="the web interface host IP address",
    )
    parser.add_argument(
        "--port", "-p", type=int, default=4909, help="the web interface port"
    )

    parser.add_argument(
        "--version", "-v", action="store_true", help="print the httpdbg version"
    )

    parser.add_argument(
        "--initiator", "-i", action="append", help="add a new initiator (package)"
    )

    server_state = parser.add_mutually_exclusive_group()

    server_state.add_argument(
        "--keep-up",
        "-k",
        action="store_true",
        help="keep the server up even if the requests have been read",
    )

    server_state.add_argument(
        "--force-quit",
        "-q",
        action="store_true",
        help="stop the server even if the requests have not been read",
    )

    parser.add_argument(
        "--log-level",
        type=LogLevel,
        choices=LogLevel,
        default=LogLevel.WARNING,
        help="The log level",
    )

    parser.add_argument("--log", type=Path, help="Path to the log file.")

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        "--console", action="store_true", help="run a python console (default)"
    )

    actions.add_argument(
        "--module",
        "-m",
        type=str,
        help="run library module as a script (the next args are passed to pytest as is)",
    )

    actions.add_argument(
        "--script",
        type=str,
        help="run a script (the next args are passed to the script as is)",
    )

    return parser.parse_args(httpdbg_args), client_args
