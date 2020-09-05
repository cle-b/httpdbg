# -*- coding: utf-8 -*-
import code
import readline  # noqa: F401 enable the 'up arrow' history in the console

from .httpdb import httpdbg


def console_exit():
    raise SystemExit


@httpdbg
def console():
    try:
        code.InteractiveConsole(locals={"exit": console_exit}).interact()
    except SystemExit:
        pass


if __name__ == "__main__":

    print("httpdbg - recorded requests available at http://localhost:5000/ ")

    console()
