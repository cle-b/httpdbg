# -*- coding: utf-8 -*-
import code
from typing import Union


def console_exit():
    raise SystemExit


def run_console(test_mode: bool = False) -> Union[code.InteractiveConsole, None]:
    try:
        vars = globals()
        vars.update(locals())

        try:
            # adds history and autocompletion capabilities
            import readline
            import rlcompleter

            readline.set_completer(rlcompleter.Completer(vars).complete)
            readline.parse_and_bind("tab: complete")
        except ImportError:  # pragma: no cover
            # readline is not available on Windows
            pass

        vars.update({"exit": console_exit})

        new_console = code.InteractiveConsole(vars)
        if not test_mode:
            new_console.interact()  # pragma: no cover
        else:
            new_console.push("print('test_mode is on')")
            return new_console
    except SystemExit:  # pragma: no cover
        pass

    return None
