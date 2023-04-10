# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os
import platform
import traceback
from typing import Generator
from typing import List
from typing import Tuple
from typing import Union

from httpdbg.hooks.utils import getcallargs
from httpdbg.utils import get_new_uuid


class Initiator(object):
    def __init__(
        self,
        id: str,
        short_label: str,
        long_label: Union[str, None],
        short_stack: str,
        stack: List[str],
    ):
        self.id = id
        self.short_label = short_label
        self.long_label = long_label
        self.short_stack = short_stack
        self.stack = stack

    def __eq__(self, other) -> bool:
        if type(other) == Initiator:
            return (
                self.short_label == other.short_label
                and self.long_label == other.long_label
                and self.short_stack == other.short_stack
                and self.stack == other.stack
            )
        else:
            return False

    def to_json(self, full: bool = True) -> dict:
        if full:
            json = {
                "id": self.id,
                "short_label": self.short_label,
                "long_label": self.long_label,
                "short_stack": self.short_stack,
                "stack": "\n".join(self.stack),
            }
        else:
            json = {
                "id": self.id,
                "short_label": self.short_label,
                "long_label": self.long_label,
                "short_stack": self.short_stack,
            }
        return json


def compatible_path(path: str) -> str:
    p = path
    if platform.system().lower() == "windows":
        p = path.replace("/", "\\")
    return p


def in_lib(line: str, packages: List[str] = None):
    if not packages:
        packages = ["requests", "httpx", "aiohttp", "urllib3"]
    return any(
        [
            (compatible_path(f"/site-packages/{package}/") in line)
            for package in packages
        ]
    )


def get_current_instruction(
    extracted_stack: traceback.StackSummary,
) -> Tuple[str, str, List[str]]:
    stack = []

    n_stack = -1
    framesummary = extracted_stack[-2]
    if framesummary.name == "__aenter__":
        n_stack = -2
        framesummary = extracted_stack[-3]

    instruction = ""
    short_stack = f'File "{framesummary.filename}", line {framesummary.lineno}, in {framesummary.name}\n'
    if os.path.exists(framesummary.filename) and framesummary.lineno is not None:
        instruction, s_stack = extract_short_stack_from_file(
            framesummary.filename, framesummary.lineno, 0, 8
        )
        short_stack += s_stack

        # stack
        to_include = False
        for i_stack in range(6, len(extracted_stack) + n_stack):
            last_stack = i_stack == len(extracted_stack) + n_stack - 1
            fs = extracted_stack[i_stack]
            to_include = to_include or (
                ("/site-packages/" not in fs.filename)
                and ("importlib" not in fs.filename)
            )  # remove the stack before to start the user part
            if to_include:
                _, s_stack = extract_short_stack_from_file(
                    fs.filename,
                    fs.lineno if fs.lineno else 0,
                    4 if last_stack else 0,
                    8,
                    not last_stack,
                )
                stack.append(f'File "{fs.filename}", line {fs.lineno}, \n{s_stack}')

    else:
        instruction = framesummary.line if framesummary.line else "console"
        short_stack += f"{instruction}\n"
        stack = []

    return instruction.replace("\n", " "), short_stack, stack


def extract_short_stack_from_file(
    filename: str,
    lineno: int,
    before: int,
    after: int,
    stop_if_instruction_ends: bool = True,
) -> Tuple[str, str]:
    instruction = ""
    short_stack = ""

    if os.path.exists(filename):
        with open(filename, "r") as src:
            lines = src.read().splitlines()

            # copy the lines before
            for i in range(lineno - 1 - before, lineno - 1):
                line = lines[i]
                short_stack += f" {i+1}. {line}\n"

            # try to recompose the instruction if on multi-lines
            end_of_instruction_found = False
            for i in range(max(0, lineno - 1), min(lineno - 1 + after, len(lines))):
                line = lines[i]
                if not end_of_instruction_found:
                    instruction += line.strip()
                short_stack += f" {i+1}. {line}{' <====' if (before>0 and i+1 == lineno) else ''}\n"
                nb_parenthesis = 0
                for c in instruction[instruction.find("(") :]:
                    if c == "(":
                        nb_parenthesis += 1
                    if c == ")":
                        nb_parenthesis -= 1
                    if nb_parenthesis == 0:
                        end_of_instruction_found = True
                        break
                if end_of_instruction_found and stop_if_instruction_ends:
                    break

    return instruction, short_stack


@contextmanager
def httpdbg_initiator(
    records, extracted_stack: traceback.StackSummary, original_method, *args, **kwargs
) -> Generator[Union[Initiator, None], None, None]:
    envname = f"HTTPDBG_CURRENT_INITIATOR_{records.id}"

    if not os.environ.get(envname):
        callargs = getcallargs(original_method, *args, **kwargs)
        instruction, short_stack, stack = get_current_instruction(extracted_stack)

        short_stack += (
            f"----------\n{original_method.__module__}.{original_method.__name__}(\n"
        )
        for k, v in callargs.items():
            short_stack += f"    {k}={v}\n"
        short_stack += ")"

        current_initiator = Initiator(
            get_new_uuid(), instruction, None, short_stack, stack
        )
        records._initiators[current_initiator.id] = current_initiator

        os.environ[envname] = current_initiator.id

        try:
            yield current_initiator
        except Exception:
            del os.environ[envname]
            raise

        del os.environ[envname]

    else:
        yield None
