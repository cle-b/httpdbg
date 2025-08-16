# -*- coding: utf-8 -*-
import code
from typing import Union

from httpdbg.records import HTTPRecords
from httpdbg.initiator import httpdbg_group


def console_exit():
    raise SystemExit


class InteractiveConsoleWithHistory(code.InteractiveConsole):

    def __init__(self, records: HTTPRecords, locals=None):
        self.records: HTTPRecords = records
        self.history: list[str] = []
        self.incomplete_block: bool = False
        super().__init__(locals)

    def push(self, line):
        if line:  # if the line is empty, we don't add it in the history
            if (
                self.incomplete_block
            ):  # if the latest instruction is part of a block, we group it with the previous one
                self.history[-1] += (
                    "\n          " + line
                )  # to simulate the block indentation
            else:
                self.history.append(line)

        # if the latest instruction is part of a block, the label is generic
        label = self.history[-1] if not self.incomplete_block else "(block)"

        # in the full label, we keep the last 5 instructions/blocks
        latest_history = self.history[-5:]
        if not self.incomplete_block:
            # in case of a block, we don't know which line within the block is the initiator.
            # this is why we do not mark it in that case.
            # this information is displayed in the initiator tooltip of the requests (in console, line X,)
            latest_history[-1] += " <===="

        full_label = ">>> " + "\n>>> ".join(latest_history)

        with httpdbg_group(self.records, label, full_label):
            self.incomplete_block = super().push(line)

        return self.incomplete_block


def run_console(
    records: HTTPRecords, test_mode: bool = False
) -> Union[InteractiveConsoleWithHistory, None]:
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

        new_console = InteractiveConsoleWithHistory(records, vars)
        if not test_mode:
            new_console.interact()  # pragma: no cover
        else:
            new_console.push("print('test_mode is on')")
            return new_console
    except SystemExit:  # pragma: no cover
        pass

    return None
