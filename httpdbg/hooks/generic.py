import builtins
from collections.abc import Callable
from contextlib import contextmanager
import functools
import importlib
import inspect
from types import ModuleType
from typing import Any
from typing import Generator
from typing import Union

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecords
from httpdbg.log import logger


def set_hook_for_generic_async(records: HTTPRecords, method: Any):
    logger().info(f"SET_HOOK_FOR_GENERIC_ASYNC {method}")

    async def hook(*args, **kwargs):
        with httpdbg_initiator(records, method, *args, **kwargs):
            ret = await method(*args, **kwargs)

        return ret

    return hook


def set_hook_for_generic(records: HTTPRecords, method: Any):
    logger().info(f"SET_HOOK_FOR_GENERIC {method}")

    def hook(*args, **kwargs):
        with httpdbg_initiator(records, method, *args, **kwargs):
            ret = method(*args, **kwargs)

        return ret

    return hook


@contextmanager
def hook_generic(
    records: HTTPRecords, initiators: Union[list[str], None] = None
) -> Generator[None, None, None]:
    if initiators:
        # we add a hook for a generic initiator only if the module is imported

        hooks: list[Callable] = []
        already_hooked: list[str] = []

        original_builtin_import = builtins.__import__

        def __hook__import__(
            name,
            globals=None,
            locals=None,
            fromlist=(),
            level=0,
            records=None,
            initiators=None,
            hooks=None,
            already_hooked=None,
        ):
            if initiators is None:
                raise Exception("initiators must not be None")
            if hooks is None:
                raise Exception("hooks must not be None")
            if already_hooked is None:
                raise Exception("already_hooked must not be None")

            if (
                name not in already_hooked
            ):  # avoids parsing the same module multiple times
                if (records is not None) and initiators:
                    if (name in initiators) or (
                        any(
                            [
                                name.startswith(f"{initiator}.")
                                for initiator in initiators
                            ]
                        )
                    ):
                        logger().debug(f"HOOK IMPORT {name} - fromlist={fromlist}")
                        already_hooked.append(name)
                        hooks += list_callables_from_module(records, name)

            # we temporarily restore the original built-in import function to avoid infinite recursion during import
            __custom_import = builtins.__import__
            builtins.__import__ = original_builtin_import
            r = original_builtin_import(
                name=name,
                globals=globals,
                locals=locals,
                fromlist=fromlist,
                level=level,
            )
            builtins.__import__ = __custom_import
            return r

        __hook__import_with_records_initiators_hooks_alreadyhooked__ = (
            functools.partial(
                __hook__import__,
                records=records,
                initiators=initiators,
                hooks=hooks,
                already_hooked=already_hooked,
            )
        )

        builtins.__import__ = (
            __hook__import_with_records_initiators_hooks_alreadyhooked__
        )

    yield

    if initiators:
        builtins.__import__ == original_builtin_import

        if hooks:
            for fnc in hooks:
                fnc = undecorate(fnc)


def list_callables_from_module(records: HTTPRecords, module: str) -> list[Any]:
    callables = []

    try:
        logger().info(f"LIST_CALLABLES_FROM_MODULE {module}")

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
        logger().info(f"LIST_CALLABLES_FROM_MODULE {module} - error - {str(ex)}")

    return callables


def list_callables_from_class(
    records: HTTPRecords,
    imported_module: ModuleType,
    module: str,
    classname: str,
) -> list[Any]:
    callables = []

    try:
        logger().info(f"LIST_CALLABLES_FROM_CLASS {module}.{classname}")
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
        logger().info(
            f"LIST_CALLABLES_FROM_CLASS {module}.{classname} - error - {str(ex)}"
        )

    return callables
