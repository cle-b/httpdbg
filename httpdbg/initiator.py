# -*- coding: utf-8 -*-
import os
import traceback


class Initiator(object):
    def __init__(self, short_label, long_label, stack):
        self.short_label = short_label
        self.long_label = long_label
        self.stack = stack

    def to_json(self, full=True):
        if full:
            json = {
                "short_label": self.short_label,
                "long_label": self.long_label,
                "stack": "\n".join(self.stack),
            }
        else:
            json = {"short_label": self.short_label, "long_label": self.long_label}
        return json


def get_initiator():
    short_label = ""
    long_label = ""
    stack = []
    fullstack = traceback.format_stack()

    if "PYTEST_CURRENT_TEST" in os.environ:
        long_label = " ".join(os.environ["PYTEST_CURRENT_TEST"].split(" ")[:-1])
        short_label = long_label.split("::")[-1]
        in_stack = False
        for line in fullstack[6:]:
            if "/site-packages/requests" in line:
                break
            if in_stack:
                stack.append(line)
            if "in pytest_pyfunc_call" in line or "in call_fixture_func" in line:
                in_stack = True

    else:
        if "httpdbg/mode_script.py" in "".join(
            fullstack
        ):  # TODO: find another way the detect the mode
            for line in fullstack[6:]:
                if "/site-packages/requests" in line:
                    break
                stack.append(line)
            long_label = stack[-1]
            short_label = long_label.split("\n")[1]
        else:
            short_label = ""
            long_label = ""

    return Initiator(short_label, long_label, stack)
