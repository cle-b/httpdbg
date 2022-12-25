# -*- coding: utf-8 -*-
import os
import platform
import traceback

from httpdbg.utils import get_new_uuid


class Initiator(object):
    def __init__(self, id, short_label, long_label, stack):
        self.id = id
        self.short_label = f'{short_label[:77]}{"..." if len(short_label)>76 else ""}'
        self.long_label = long_label
        self.stack = stack

    def to_json(self, full=True):
        if full:
            json = {
                "id": self.id,
                "short_label": self.short_label,
                "long_label": self.long_label,
                "stack": "\n".join(self.stack),
            }
        else:
            json = {
                "id": self.id,
                "short_label": self.short_label,
                "long_label": self.long_label,
            }
        return json


def compatible_path(path):
    p = path
    if platform.system().lower() == "windows":
        p = path.replace("/", "\\")
    return p


def in_lib(line, packages=[]):
    if not packages:
        packages = ["requests", "httpx", "aiohttp", "urllib3"]
    return any(
        [
            (compatible_path(f"/site-packages/{package}/") in line)
            for package in packages
        ]
    )


def get_initiator(initiators):
    short_label = ""
    long_label = ""
    stack = []
    fullstack = traceback.format_stack()
    id = None

    if "PYTEST_CURRENT_TEST" in os.environ:
        long_label = " ".join(os.environ["PYTEST_CURRENT_TEST"].split(" ")[:-1])
        short_label = long_label.split("::")[-1]
        in_stack = False
        for line in fullstack[6:]:
            if in_lib(line):
                break
            if in_stack:
                stack.append(line)
            if "in pytest_pyfunc_call" in line or "in call_fixture_func" in line:
                in_stack = True
        if long_label not in initiators:
            initiators[long_label] = get_new_uuid()
        id = initiators[long_label]
    else:
        if compatible_path("httpdbg/mode_script.py") in "".join(
            fullstack
        ):  # TODO: find another way the detect the mode
            for line in fullstack[6:]:
                if in_lib(line):
                    break
                stack.append(line)
            long_label = stack[-1]
            short_label = long_label.split("\n")[1]
            hashstack = hash("".join(fullstack))
            if hashstack not in initiators:
                initiators[hashstack] = get_new_uuid()
            id = initiators[hashstack]
        else:
            short_label = "console"
            long_label = "console"
            id = "console"

    return Initiator(id, short_label, long_label, stack)
