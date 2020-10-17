# -*- coding: utf-8 -*-
import readline  # noqa: F401 enable the 'up arrow' history in the console
import sys

from .httpdbg import httpdbg
from .mode_console import run_console
from .mode_pytest import run_pytest
from .mode_script import run_script


def pyhttpdbg(argv, test_mode=False):

    print("-- -- -- httpdbg - recorded requests available at http://localhost:5000/ ")

    with httpdbg():
        if len(argv) == 0:
            run_console(test_mode)
        elif argv[0] == "pytest":
            run_pytest(argv)
        else:
            run_script(argv)

        input(
            "-- -- -- httpdbg - recorded requests available at http://localhost:5000/ until you press enter"
        )


def pyhttpdbg_entry_point(test_mode=False):
    pyhttpdbg(sys.argv[1:], test_mode=test_mode)


if __name__ == "__main__":
    pyhttpdbg(sys.argv[1:])
