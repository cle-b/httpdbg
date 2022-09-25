# -*- coding: utf-8 -*-
import argparse


def read_args(args):
    parser = argparse.ArgumentParser(
        description="httdbg - a very simple tool to debug HTTP client requests"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=4909, help="the web interface port"
    )
    parser.add_argument(
        "--terminate",
        "-t",
        type=int,
        default=-1,
        help="delay in second before stopping the web interface after the end (-1 means infinity)",
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
