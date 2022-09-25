# -*- coding: utf-8 -*-
try:
    import readline  # noqa: F401 enable the 'up arrow' history in the console
except ImportError:
    pass  # readline is not available on Windows
import sys
import time

from httpdbg.args import read_args
from httpdbg.server import httpdbg
from httpdbg.mode_console import run_console
from httpdbg.mode_pytest import run_pytest
from httpdbg.mode_script import run_script
from httpdbg.webapp import httpdebugk7


def pyhttpdbg(params, subparams, test_mode=False):

    url = f"http://localhost:{params.port}/{'?hi=on' if params.console else ''}"

    print(f"-- -- -- httpdbg - recorded requests available at {url} ")

    with httpdbg(params.port):

        if params.pytest:
            run_pytest(subparams)
        elif params.script:
            run_script(subparams)
        else:
            run_console(test_mode)

        if params.terminate == -1:
            input(
                f"-- -- -- httpdbg - recorded requests available at {url} until you press enter"
            )
        else:
            print(
                f"-- -- -- httpdbg - recorded requests available at {url} for {params.terminate} seconds"
            )
            tend = time.time() + (params.terminate)
            while time.time() < tend:
                time.sleep(1)
                # if all the requests have been download in the webpage, we prematurarly stop the python process
                if set(httpdebugk7["requests"]["available"]) == set(
                    httpdebugk7["requests"]["getted"]
                ):
                    break


def pyhttpdbg_entry_point(test_mode=False):
    params, subparams = read_args(sys.argv[1:])
    pyhttpdbg(params, subparams, test_mode=test_mode)


if __name__ == "__main__":
    pyhttpdbg_entry_point()
