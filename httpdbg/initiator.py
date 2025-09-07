# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import datetime
import inspect
import os
import platform
import traceback
from typing import Generator
from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpdbg.records import HTTPRecords

from httpdbg.hooks.utils import getcallargs
from httpdbg.utils import get_new_uuid
from httpdbg.log import logger


class Initiator:
    def __init__(
        self,
        label: str,
        short_stack: str,
        stack: list[str],
    ):
        self.id = get_new_uuid()
        self.label = label
        self.short_stack = short_stack
        self.stack = stack
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

    def __eq__(self, other) -> bool:
        if type(other) is Initiator:
            return (
                self.label == other.label
                and self.short_stack == other.short_stack
                and self.stack == other.stack
            )
        else:
            return False

    def to_json(self, full: bool = True) -> dict:
        if full:
            json = {
                "id": self.id,
                "label": self.label,
                "short_stack": self.short_stack,
                "stack": "\n".join(self.stack),
                "tbegin": self.tbegin.isoformat(),
            }
        else:
            json = {
                "id": self.id,
                "label": self.label,
                "short_stack": self.short_stack,
                "tbegin": self.tbegin.isoformat(),
            }
        return json


class Group:
    def __init__(self, label: str, full_label: str, updatable: bool):
        self.id: str = get_new_uuid()
        self.label: str = label
        self.full_label: str = full_label
        self.updatable: bool = updatable
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "full_label": self.full_label,
            "tbegin": self.tbegin.isoformat(),
        }


def compatible_path(path: str) -> str:
    p = path
    if platform.system().lower() == "windows":
        p = path.replace("/", "\\")
    return p


def in_lib(line: str, packages: list[str] = None):
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
) -> tuple[str, str, list[str]]:
    instruction = ""
    short_stack = ""
    stack = []

    try:
        n_stack = -2
        framesummary = extracted_stack[-3]

        while (
            ("httpdbg/hooks" in framesummary.filename)
            or ("httpdbg\\hooks" in framesummary.filename)
            or ("asyncio" in framesummary.filename)
        ):
            n_stack -= 1
            framesummary = extracted_stack[n_stack - 1]

        short_stack = f'File "{framesummary.filename}", line {framesummary.lineno}, in {framesummary.name}\n'
        if os.path.exists(framesummary.filename) and framesummary.lineno is not None:
            instruction, s_stack = extract_short_stack_from_file(
                framesummary.filename, framesummary.lineno, 0, 8
            )
            short_stack += s_stack

            # stack
            to_include = False
            for i_stack in range(7, len(extracted_stack) + n_stack):
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
    except Exception as ex:
        logger().info(
            f"GET_CURRENT_INSTRUCTION [{str(extracted_stack)}] - error - {str(ex)}"
        )

    return instruction.replace("\n", " "), short_stack, stack


def extract_short_stack_from_file(
    filename: str,
    lineno: int,
    before: int,
    after: int,
    stop_if_instruction_ends: bool = True,
) -> tuple[str, str]:
    instruction = ""
    short_stack = ""

    try:
        if os.path.exists(filename):
            with open(filename, "r") as src:
                lines = src.read().splitlines()

                # copy the lines before
                for i in range(
                    max(0, lineno - 1 - before), min(lineno - 1, len(lines))
                ):
                    line = lines[i]
                    short_stack += f" {i+1}. {line}\n"

                # try to recompose the instruction if on multi-lines
                end_of_instruction_found = False
                for i in range(max(0, lineno - 1), min(lineno - 1 + after, len(lines))):
                    line = lines[i]
                    if not end_of_instruction_found:
                        instruction += line.strip()
                    short_stack += f" {i+1}. {line}{' <====' if (before > 0 and i + 1 == lineno) else ''}\n"
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
    except Exception as ex:
        logger().info(
            f"EXTRACT_SHORT_STACK_FROM_FILE {filename} lineno={lineno} before={before} after={after}- error - {str(ex)}"
        )

    return instruction, short_stack


def construct_call_str(original_method, *args, **kwargs):

    def print_v(v) -> str:
        try:
            if isinstance(v, str):
                return f'"{v}"'
            else:
                return str(v)
        except Exception:
            return "-?-"  # in case __retr__ or __str__ is broken

    callargs = getcallargs(original_method, *args, **kwargs)

    str_module = (
        f"{original_method.__module__}."
        if hasattr(original_method, "__module__")
        else ""
    )
    str_name = (
        f"{original_method.__name__}" if hasattr(original_method, "__name__") else "***"
    )

    if callargs:
        r = f"{str_module}{str_name}(\n"
        for k, v in callargs.items():
            r += f"    {k}={print_v(v)},\n"
        r += ")"
    else:
        r = f"{str_module}{str_name}()"

    return r


@contextmanager
def httpdbg_initiator(
    records: "HTTPRecords",
    original_method: Callable,
    *args,
    **kwargs,
) -> Generator[tuple[Initiator, Group, bool], None, None]:
    try:
        if records.current_initiator is None:
            initiator_already_set = False

            extracted_stack: traceback.StackSummary = traceback.extract_stack()

            # temporary set a fake initiator env variable to avoid a recursion error
            #  RecursionError: maximum recursion depth exceeded while calling a Python object
            # TL;DR When we construct the short_stack string, a recursion error occurs if there
            # is an object from a class where a hooked method is called in __repr__ or __str__.
            records.current_initiator = "--fakeinitiator--"
            instruction, short_stack, stack = get_current_instruction(extracted_stack)
            short_stack += "----------\n" + construct_call_str(
                original_method, *args, **kwargs
            )

            current_initiator = Initiator(instruction, short_stack, stack)

            records.add_initiator(current_initiator)
        else:
            initiator_already_set = True
            if records.current_initiator != "--fakeinitiator--":
                current_initiator = records.initiators[records.current_initiator]
            else:
                # this fake initiator does not need to be recorded
                current_initiator = Initiator("", "", [])

        with httpdbg_group(
            records, current_initiator.label, current_initiator.short_stack
        ) as group:  # by default we group the requests by initiator
            yield current_initiator, group, initiator_already_set is False
    except Exception:
        raise
    finally:
        # import to make the context manager reentrant
        if not initiator_already_set:
            records.current_initiator = None


@contextmanager
def httpdbg_tag(records: "HTTPRecords", tag: str) -> Generator[None, None, None]:

    if records.current_tag is None:
        tag_already_set = False
        logger().info("httpdbg_tag (new)")
        records.current_tag = tag
    else:
        tag_already_set = True

    try:
        logger().info(f"httpdbg_tag {tag}")
        yield
    except Exception:
        if not tag_already_set:
            records.current_tag = None
        raise

    if not tag_already_set:
        records.current_tag = None


@contextmanager
def httpdbg_group(
    records: "HTTPRecords",
    label: str,
    full_label: str,
    update: bool = False,
    updatable: bool = True,
) -> Generator[Group, None, None]:

    if records.current_group is None:
        group_already_set = False
        logger().info("httpdbg_group (new)")
        group = Group(label, full_label, updatable=updatable)
        records.add_group(group)
    else:
        group_already_set = True
        group = records.groups[records.current_group]

    if update and group.updatable:
        # Update the label and full_label of an existing group, in case of endpoint.
        group.label = label
        group.full_label = full_label
    try:
        logger().info(
            f"httpdbg_group {group} group_id={records.current_group} label={label} full_label={full_label}"
        )
        yield group
    except Exception:
        if not group_already_set:
            records.current_group = None
        raise

    if not group_already_set:
        records.current_group = None


@contextmanager
def httpdbg_endpoint(
    records: "HTTPRecords", original_method: Callable, *args, **kwargs
) -> Generator[Union[Group, None], None, None]:

    filename = inspect.getsourcefile(original_method)
    if filename:
        _, lineno = inspect.getsourcelines(original_method)
        instruction, s_stack = extract_short_stack_from_file(filename, lineno, 0, 8)
        full_label = (
            f'File "{filename}", line {lineno}, in {original_method.__name__}\n'
        )
        full_label += s_stack
        full_label += "----------\n" + construct_call_str(
            original_method, *args, **kwargs
        )

        with httpdbg_group(records, instruction, full_label, update=True) as group:
            yield group
    else:
        yield None
