# -*- coding: utf-8 -*-
from contextlib import contextmanager
import glob
import importlib
import inspect
from pathlib import Path
import traceback
from typing import Generator
from typing import List
from typing import Union

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecords
from httpdbg.utils import logger


def set_hook_for_generic_async(records, method):
    async def hook(*args, **kwargs):
        with httpdbg_initiator(
            records, traceback.extract_stack(), method, *args, **kwargs
        ):
            ret = await method(*args, **kwargs)

        return ret

    return hook


def set_hook_for_generic(records, method):
    def hook(*args, **kwargs):
        with httpdbg_initiator(
            records, traceback.extract_stack(), method, *args, **kwargs
        ):
            ret = method(*args, **kwargs)

        return ret

    return hook


@contextmanager
def hook_generic(
    records: HTTPRecords, initiators: Union[List[str], None] = None
) -> Generator[None, None, None]:
    hooks = []

    if not initiators:
        initiators = []

    for initiator in initiators:
        logger.debug(f"HOOK_GENERIC add package - {initiator}")
        try:
            hooks += list_callables_from_package(records, initiator)
        except Exception as ex:
            logger.debug(f"HOOK_GENERIC exception - {str(ex)}")

    yield

    if hooks:
        for fnc in hooks:
            fnc = undecorate(fnc)


def list_callables_from_package(records, package):
    callables = []

    callables += list_callables_from_module(records, package)

    try:
        imported_package = importlib.import_module(package)
        for p in glob.glob(f"{imported_package.__path__[0]}/*"):
            file_or_dir = Path(p)
            if file_or_dir.is_file():
                if file_or_dir.name.endswith(".py"):
                    callables += list_callables_from_module(
                        records, f"{package}.{file_or_dir.name[:-3]}"
                    )
            elif file_or_dir.is_dir():
                if not file_or_dir.name.startswith("__"):  # __pycache__
                    callables += list_callables_from_package(
                        records, f"{package}.{file_or_dir.name}"
                    )
    except ImportError:
        pass

    return callables


def list_callables_from_module(records, module):
    callables = []

    imported_module = importlib.import_module(module)

    for name in imported_module.__dict__.keys():
        # hook must be applied only on function/method defined in the current module (not imported)
        from_module = getattr(imported_module.__dict__[name], "__module__", "")
        if from_module and from_module.startswith(module):
            # a coroutine is a function so this condition must be checked first
            if inspect.iscoroutinefunction(imported_module.__dict__[name]):
                imported_module.__dict__[name] = decorate(
                    records,
                    imported_module.__dict__[name],
                    set_hook_for_generic_async,
                )
                callables.append(imported_module.__dict__[name])

            elif inspect.isfunction(imported_module.__dict__[name]):
                imported_module.__dict__[name] = decorate(
                    records,
                    imported_module.__dict__[name],
                    set_hook_for_generic,
                )
                callables.append(imported_module.__dict__[name])

            elif inspect.isclass(imported_module.__dict__[name]):
                callables += list_callables_from_class(
                    records, imported_module, module, name
                )

    return callables


def list_callables_from_class(records, imported_module, module, classname):
    callables = []

    for name in imported_module.__dict__[classname].__dict__.keys():
        from_module = getattr(
            imported_module.__dict__[classname].__dict__[name], "__module__", ""
        )
        if from_module and from_module.startswith(module):
            if not name.startswith("__"):
                if inspect.iscoroutinefunction(
                    imported_module.__dict__[classname].__dict__[name]
                ):
                    hook = decorate(
                        records,
                        imported_module.__dict__[classname].__dict__[name],
                        set_hook_for_generic_async,
                    )
                    setattr(
                        imported_module.__dict__[classname], name, hook
                    )  # TypeError: 'mappingproxy' object does not support item assignment
                    callables.append(hook)

                elif inspect.isfunction(
                    imported_module.__dict__[classname].__dict__[name]
                ):
                    hook = decorate(
                        records,
                        imported_module.__dict__[classname].__dict__[name],
                        set_hook_for_generic,
                    )
                    setattr(imported_module.__dict__[classname], name, hook)
                    callables.append(hook)

    return callables