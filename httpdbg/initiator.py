# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import datetime
import inspect
import os
import platform
import traceback
from typing import Generator
from typing import List
from typing import Tuple
from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpdbg.records import HTTPRecords

from httpdbg.env import HTTPDBG_CURRENT_GROUP
from httpdbg.env import HTTPDBG_CURRENT_INITIATOR
from httpdbg.env import HTTPDBG_CURRENT_TAG
from httpdbg.hooks.utils import getcallargs
from httpdbg.utils import get_new_uuid
from httpdbg.log import logger


class Initiator:
    def __init__(
        self,
        label: str,
        short_stack: str,
        stack: List[str],
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
    instruction = ""
    short_stack = ""
    stack = []

    try:
        n_stack = -1
        framesummary = extracted_stack[-2]
        while "asyncio" in framesummary.filename:
            n_stack -= 1
            framesummary = extracted_stack[n_stack - 1]

        while ("httpdbg/hooks" in framesummary.filename) or (
            "httpdbg\\hooks" in framesummary.filename
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
) -> Tuple[str, str]:
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

    def print_v(v):
        if isinstance(v, str):
            return f'"{v}"'
        else:
            return v

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
    extracted_stack: traceback.StackSummary,
    original_method: Callable,
    *args,
    **kwargs,
) -> Generator[Union[Tuple[Initiator, Group, bool], None], None, None]:
    # An initiator is considered set if the environment variable exists and the initiator
    # is recorded.If the environment variable exists but the initiatir is not recorded,
    # it means httpdbg was called reentrantly, and we need to record the initiator again
    # using the same id.
    initiator_already_set = (HTTPDBG_CURRENT_INITIATOR in os.environ) and (
        os.environ[HTTPDBG_CURRENT_INITIATOR] in records.initiators
    )
    try:
        if not initiator_already_set:
            original_initiator_id = None
            if HTTPDBG_CURRENT_INITIATOR not in os.environ:
                # temporary set a fake initiator env variable to avoid a recursion error
                #  RecursionError: maximum recursion depth exceeded while calling a Python object
                # TL;DR When we construct the short_stack string, a recursion error occurs if there
                # is an object from a class where a hooked method is called in __repr__ or __str__.
                os.environ[HTTPDBG_CURRENT_INITIATOR] = "blabla"
            else:
                original_initiator_id = os.environ[HTTPDBG_CURRENT_INITIATOR]

            # in any case, we create an Initiator
            instruction, short_stack, stack = get_current_instruction(extracted_stack)
            short_stack += "----------\n" + construct_call_str(
                original_method, *args, **kwargs
            )

            current_initiator = Initiator(instruction, short_stack, stack)

            if original_initiator_id:
                # if we already have an initiator id (reentrant call) we change the initiator id
                # to keep the same
                current_initiator.id = original_initiator_id

            records.initiators[current_initiator.id] = current_initiator

            os.environ[HTTPDBG_CURRENT_INITIATOR] = current_initiator.id

        else:
            current_initiator = records.initiators[
                os.environ[HTTPDBG_CURRENT_INITIATOR]
            ]

        with httpdbg_group(
            records, current_initiator.label, current_initiator.short_stack
        ) as group:  # by default we group the requests by initiator
            yield current_initiator, group, initiator_already_set is False
    except Exception:
        if (not initiator_already_set) and (HTTPDBG_CURRENT_INITIATOR in os.environ):
            del os.environ[HTTPDBG_CURRENT_INITIATOR]
        raise

    if (not initiator_already_set) and (HTTPDBG_CURRENT_INITIATOR in os.environ):
        del os.environ[HTTPDBG_CURRENT_INITIATOR]


@contextmanager
def httpdbg_tag(tag: str) -> Generator[None, None, None]:

    tag_already_set = HTTPDBG_CURRENT_TAG in os.environ

    if not tag_already_set:
        os.environ[HTTPDBG_CURRENT_TAG] = tag

    try:
        logger().info(f"httpdbg_tag {tag}")
        yield
    except Exception:
        if (not tag_already_set) and (HTTPDBG_CURRENT_TAG in os.environ):
            del os.environ[HTTPDBG_CURRENT_TAG]
        raise

    if (not tag_already_set) and (HTTPDBG_CURRENT_TAG in os.environ):
        del os.environ[HTTPDBG_CURRENT_TAG]


@contextmanager
def httpdbg_group(
    records: "HTTPRecords",
    label: str,
    full_label: str,
    update: bool = False,
    updatable: bool = True,
) -> Generator[Group, None, None]:

    # A group is considered set if the environment variable exists and the group
    # is recorded.If the environment variable exists but the group is not recorded,
    # it means httpdbg was called reentrantly, and we need to record the group again
    # using the same id.
    group_already_set = (HTTPDBG_CURRENT_GROUP in os.environ) and (
        os.environ[HTTPDBG_CURRENT_GROUP] in records.groups
    )

    if not group_already_set:
        logger().info("httpdbg_group (new)")
        group = Group(label, full_label, updatable=updatable)
        # in case of a reentrant call to httpdbg, we force the group id to be the same
        if HTTPDBG_CURRENT_GROUP in os.environ:
            group.id = os.environ[HTTPDBG_CURRENT_GROUP]
            logger().info("httpdbg_group (reentrant) keep id {group.id}")
        records.groups[group.id] = group
        os.environ[HTTPDBG_CURRENT_GROUP] = group.id
    else:
        group = records.groups[os.environ[HTTPDBG_CURRENT_GROUP]]

    if update and group.updatable:
        # Update the label and full_label of an existing group, in case of endpoint.
        group.label = label
        group.full_label = full_label
    try:
        logger().info(
            f"httpdbg_group {group} group_id={os.environ[HTTPDBG_CURRENT_GROUP]} label={label} full_label={full_label}"
        )
        yield group
    except Exception:
        if (not group_already_set) and (HTTPDBG_CURRENT_GROUP in os.environ):
            del os.environ[HTTPDBG_CURRENT_GROUP]
        raise

    if (not group_already_set) and (HTTPDBG_CURRENT_GROUP in os.environ):
        del os.environ[HTTPDBG_CURRENT_GROUP]


@contextmanager
def httpdbg_endpoint(
    records: "HTTPRecords", original_method: Callable, *args, **kwargs
) -> Generator[None, None, None]:

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

        with httpdbg_group(records, instruction, full_label, update=True):
            yield
    else:
        yield
