# -*- coding: utf-8 -*-
import argparse


def read_args(args):
    parser = argparse.ArgumentParser(
        description="httdbg - a very simple tool to debug HTTP client requests"
    )
    parser.add_argument(
        "--port", "-p", type=int, default=5000, help="the web interface port"
    )
    parser.add_argument(
        "--terminate",
        "-t",
        type=int,
        default=-1,
        help="delay in second before stopping the web interface after the end (-1 means infinity)",
    )

    if "--" in args:
        # if there is the argument "--" then all the arguments before
        # this one are related to httpdbg
        httpdbg_args = args[: args.index("--")]
        client_args = args[args.index("--") + 1 :]
    else:
        httpdbg_args = []
        client_args = args

    return parser.parse_args(httpdbg_args), client_args
