# -*- coding: utf-8 -*-
import code


def console_exit():
    raise SystemExit


def run_console(test_mode=False):
    try:
        new_console = code.InteractiveConsole(locals={"exit": console_exit})
        if not test_mode:
            new_console.interact()  # pragma: no cover
        else:
            return new_console
    except SystemExit:  # pragma: no cover
        pass
