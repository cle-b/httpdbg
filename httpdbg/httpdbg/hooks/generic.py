# -*- coding: utf-8 -*-
from contextlib import contextmanager
import glob
import importlib
import inspect
from pathlib import Path
import traceback
from types import ModuleType
from typing import Any
from typing import Generator
from typing import List
from typing import Union

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecords
from httpdbg.utils import logger


def set_hook_for_generic_async(records: HTTPRecords, method: Any):
    logger.info(f"SET_HOOK_FOR_GENERIC_ASYNC {method}")

    async def hook(*args, **kwargs):
        with httpdbg_initiator(
            records, traceback.extract_stack(), method, *args, **kwargs
        ):
            ret = await method(*args, **kwargs)

        return ret

    return hook


def set_hook_for_generic(records: HTTPRecords, method: Any):
    logger.info(f"SET_HOOK_FOR_GENERIC {method}")

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
        logger.info(f"HOOK_GENERIC add initiator - {initiator}")
        hooks += list_callables_from_package(records, initiator)

    try:
        logger.info(
            f"HOOK_GENERIC add initiator - hooks - {[hook.__httpdbg__.__name__ for hook in hooks]}"
        )
    except Exception:
        pass

    yield

    if hooks:
        for fnc in hooks:
            fnc = undecorate(fnc)


def list_callables_from_package(records: HTTPRecords, package: str) -> List[Any]:
    callables = []

    try:
        logger.info(f"LIST_CALLABLES_FROM_PACKAGE {package}")

        callables += list_callables_from_module(records, package)

        imported_package = importlib.import_module(package)
        if hasattr(imported_package, "__path__"):
            for p in glob.glob(f"{list(imported_package.__path__)[0]}/*"):
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
    except Exception as ex:
        logger.info(f"LIST_CALLABLES_FROM_PACKAGE {package} - error - {str(ex)}")

    return callables


def list_callables_from_module(records: HTTPRecords, module: str) -> List[Any]:
    callables = []

    try:
        logger.info(f"LIST_CALLABLES_FROM_MODULE {module}")

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
                    if name.startswith("pytest_"):
                        # An error occurs when executing the pytest module if a pytest hook is included in a package selected as initiator
                        # (ex: pyhttpdbg -i package_with_conftest_that_contains_pytest_hooks -m pytest test_hello.py).
                        # => TypeError: pytest_addoption() missing 1 required positional argument: 'parser'
                        # To avoid it, we never add a hook on the pytest hook functions
                        continue
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
    except Exception as ex:
        logger.info(f"LIST_CALLABLES_FROM_MODULE {module} - error - {str(ex)}")

    return callables


def list_callables_from_class(
    records: HTTPRecords,
    imported_module: ModuleType,
    module: str,
    classname: str,
) -> List[Any]:
    callables = []

    try:
        logger.info(f"LIST_CALLABLES_FROM_CLASS {module}.{classname}")
        for name in imported_module.__dict__[classname].__dict__.keys():
            from_module = getattr(
                imported_module.__dict__[classname].__dict__[name], "__module__", ""
            )
            if from_module and from_module.startswith(module):
                if name == "teardown_method":
                    # An error occurs when executing the pytest module if a test class inherits from a class included in a
                    # package selected as initiator (ex: pyhttpdbg -i package_with_base_test_class -m pytest test_with_class.py).
                    # => TypeError: BaseTestClass.teardown_method() takes 1 positional argument but 2 were given
                    # To avoid it, we never add a hook on the "teardown_method" methods
                    continue
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
    except Exception as ex:
        logger.info(
            f"LIST_CALLABLES_FROM_CLASS {module}.{classname} - error - {str(ex)}"
        )

    return callables
