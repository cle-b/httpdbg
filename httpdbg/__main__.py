# -*- coding: utf-8 -*-
try:
    import readline  # noqa: F401 enable the 'up arrow' history in the console
except ImportError:
    pass  # readline is not available on Windows
import sys
import time

from .args import read_args
from .httpdbg import httpdbg
from .mode_console import run_console
from .mode_pytest import run_pytest
from .mode_script import run_script
from .webapp import httpdebugk7


def pyhttpdbg(port, delay_after_end, argv, test_mode=False):

    print(
        f"-- -- -- httpdbg - recorded requests available at http://localhost:{port}/ "
    )

    with httpdbg(port):
        if len(argv) == 0:
            run_console(test_mode)
        elif argv[0] == "pytest":
            run_pytest(argv)
        else:
            run_script(argv)

        if delay_after_end == -1:
            input(
                f"-- -- -- httpdbg - recorded requests available at http://localhost:{port}/ until you press enter"
            )
        else:
            print(
                f"-- -- -- httpdbg - recorded requests available at http://localhost:{port}/ for {delay_after_end} seconds"
            )
            tend = time.time() + (delay_after_end)
            while time.time() < tend:
                time.sleep(1)
                # if all the requests have been download in the webpage, we prematurarly stop the python process
                if set(httpdebugk7["requests"]["available"]) == set(
                    httpdebugk7["requests"]["getted"]
                ):
                    break


def pyhttpdbg_entry_point(test_mode=False):
    params, args = read_args(sys.argv[1:])
    pyhttpdbg(params.port, params.terminate, args, test_mode=test_mode)


if __name__ == "__main__":
    params, args = read_args(sys.argv[1:])
    pyhttpdbg(params.port, params.terminate, args)
