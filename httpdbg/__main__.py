# -*- coding: utf-8 -*-
import code
import importlib.util
import readline  # noqa: F401 enable the 'up arrow' history in the console
import sys

from .httpdbg import httpdbg


def console_exit():
    raise SystemExit


def console():
    try:
        code.InteractiveConsole(locals={"exit": console_exit}).interact()
    except SystemExit:
        pass


def pyhttpdbg():

    print("-- -- -- httpdbg - recorded requests available at http://localhost:5000/ ")

    argv = sys.argv[1:]

    with httpdbg():
        if len(argv) == 0:
            console()
        elif argv[0] == "pytest":
            sys.argv = argv
            try:
                import pytest

                pytest.main()
            except Exception as exp:
                print(exp)
            input(
                "-- -- -- httpdbg - recorded requests available at http://localhost:5000/ until you press enter"
            )
        else:
            sys.argv = argv
            try:
                spec = importlib.util.spec_from_file_location("torun", argv[0])
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as exp:
                print(exp)
            input(
                "-- -- -- httpdbg - recorded requests available at http://localhost:5000/ until you press enter"
            )


if __name__ == "__main__":
    pyhttpdbg()
