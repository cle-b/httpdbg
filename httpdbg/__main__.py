import argparse
from pathlib import Path
import sys
import time
from typing import Union

from httpdbg import __version__
from httpdbg.args import read_args
from httpdbg.export import export_html
from httpdbg.hooks.all import httprecord
from httpdbg.log import set_env_for_logging
from httpdbg.server import httpdbg_srv
from httpdbg.mode_console import run_console
from httpdbg.mode_module import run_module
from httpdbg.mode_script import run_script
from httpdbg.records import HTTPRecords


def print_msg(msg):
    sep = ".... - - .--. -.. -... --. .... - - .--. -.. -... --. .... - - .--. -.. -... --."
    msg = f"{sep}\n{msg}\n{sep}"
    print(msg)


def pyhttpdbg(
    params: argparse.Namespace, subparams: list[str], test_mode: bool = False
):

    set_env_for_logging(params.log_level, params.log)

    sys.path.insert(0, "")  # to mimic the default python command behavior

    def run_recorder(
        records: HTTPRecords,
        initiators: Union[list[str], None],
        record_server: bool,
        test_mode: bool,
    ):
        records.server = record_server
        with httprecord(records, initiators, server=records.server):
            if params.module:
                run_module(subparams)
            elif params.script:
                run_script(subparams)
            else:
                run_console(records, test_mode)

    if params.export_html:
        records = HTTPRecords()

        run_recorder(records, params.initiator, not params.only_client, test_mode)

        export_html(records, Path(params.export_html))

    else:
        url = f"http://{params.host}:{params.port}/{'?hi=on' if params.console else ''}"

        if not params.no_banner:
            print_msg(f"  httpdbg - HTTP(S) requests available at {url}")

        with httpdbg_srv(params.host, params.port) as records:

            run_recorder(records, params.initiator, not params.only_client, test_mode)

            if not (params.force_quit or test_mode):
                if not params.no_banner:
                    print_msg(f"  httpdbg - HTTP(S) requests available at {url}")

                if params.keep_up:
                    input("Press enter to quit")
                else:
                    # we keep the server up until all the requests have been loaded in the web interface
                    print(
                        "Waiting until all the requests have been loaded in the web interface."
                    )
                    print("Press Ctrl+C to quit.")
                    try:
                        while records.unread:
                            time.sleep(0.5)
                    except KeyboardInterrupt:  # pragma: no cover
                        pass


def pyhttpdbg_entry_point(test_mode=False):
    params, subparams = read_args(sys.argv[1:])
    if params.version:
        print(__version__)
    else:
        pyhttpdbg(params, subparams, test_mode=test_mode)


if __name__ == "__main__":
    pyhttpdbg_entry_point()
