# -*- coding: utf-8 -*-
import argparse


def read_args(args):
    parser = argparse.ArgumentParser(
        description="httdbg - a very simple tool to debug HTTP(S) client requests"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=4909, help="the web interface port"
    )

    parser.add_argument(
        "--version", "-v", action="store_true", help="print the httpdbg version"
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

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument("--console", action="store_true", help="run a python console")

    actions.add_argument(
        "--pytest",
        action="store_true",
        help="run pytest (the next args are passed to pytest as is)",
    )

    actions.add_argument(
        "--script",
        action="store_true",
        help="run the script that follows this arg (the next args are passed to the script as is)",
    )

    httpdbg_args = args
    client_args = []
    for action in ["--console", "--pytest", "--script"]:
        if action in args:
            httpdbg_args = args[: args.index(action) + 1]
            client_args = args[args.index(action) + 1 :]
            break

    return parser.parse_args(httpdbg_args), client_args
