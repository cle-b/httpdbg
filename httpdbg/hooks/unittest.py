# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import inspect
import os
import typing
from typing import Generator

from httpdbg.initiator import httpdbg_group
from httpdbg.initiator import httpdbg_tag
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.records import HTTPRecords


def set_hook_for_unittest_run(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        if "self" in callargs:
            test_case = callargs["self"]

            label = "unknown test"
            full_label = "unknown test"

            method_name = getattr(test_case, "_testMethodName")
            if method_name:
                test_class_name = test_case.__class__.__name__
                label = f"{test_class_name}::{method_name}"
                full_label = label
                test_module = inspect.getmodule(test_case.__class__)
                test_module_path = getattr(test_module, "__file__")
                if test_module_path:
                    test_module_path = os.path.relpath(test_module_path)
                    full_label = f"{test_module_path}::{full_label}"

            with httpdbg_group(records, label, full_label, updatable=False):
                ret = method(*args, **kwargs)
        else:
            ret = method(*args, **kwargs)
        return ret

    return hook


def set_hook_for_unittest_fixture(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):

        if getattr(method, "__name__") == "_callSetUp":
            with httpdbg_tag(records, "setUp"):
                return method(*args, **kwargs)
        elif getattr(method, "__name__") == "_callTearDown":
            with httpdbg_tag(records, "tearDown"):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


def set_hook_for_unittest_class_setup(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        if "test" in callargs:
            test_case = callargs["test"]

            test_class_name = test_case.__class__.__name__
            label = f"{test_class_name}::setUpClass"
            full_label = label

            test_module = inspect.getmodule(test_case.__class__)
            test_module_path = getattr(test_module, "__file__")
            if test_module_path:
                test_module_path = os.path.relpath(test_module_path)
                full_label = f"{test_module_path}::{full_label}"

            with httpdbg_group(records, label, full_label, updatable=False):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


def set_hook_for_unittest_class_teardown(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        test_result = None
        if "result" in callargs:
            result = callargs["result"]

            if result.testsRun > 0:
                test_result = result

        if test_result:

            label = "tearDownClass (unknown class)"
            full_label = label

            test_class = getattr(test_result, "_previousTestClass")
            if test_class:
                test_class_name = test_class.__name__
                label = f"{test_class_name}::tearDownClass"
                full_label = label

                test_module = inspect.getmodule(test_class)
                test_module_path = getattr(test_module, "__file__")
                if test_module_path:
                    test_module_path = os.path.relpath(test_module_path)
                    full_label = f"{test_module_path}::{full_label}"

            with httpdbg_group(records, label, full_label, updatable=False):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


def set_hook_for_unittest_module_setup(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        if "test" in callargs:
            test_suite = callargs["test"]

            test_module = inspect.getmodule(test_suite)

            if test_module:
                label = f"setUpModule ({test_module.__name__})"  # may be __main__
                full_label = label

                test_module_path = getattr(test_module, "__file__")
                if test_module_path:
                    # if we execute the tests using the script mode, the module name is __main__
                    # this is why we retrieve the module name from the path
                    module_name = os.path.splitext(os.path.basename(test_module_path))[
                        0
                    ]
                    label = f"setUpModule ({module_name})"

                    test_module_path = os.path.relpath(test_module_path)
                    full_label = f"{test_module_path}::setUpModule"

                with httpdbg_group(records, label, full_label, updatable=False):
                    return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


def set_hook_for_unittest_module_teardown(records: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        test_result = None
        if "result" in callargs:
            result = callargs["result"]

            if result.testsRun > 0:
                test_result = result

        if test_result:

            label = "tearDownModule (unknown module)"
            full_label = label

            test_class = getattr(test_result, "_previousTestClass")
            if test_class:

                test_module = inspect.getmodule(test_class)

                if test_module:
                    label = (
                        f"tearDownModule ({test_module.__name__})"  # may be __main__
                    )

                    test_module_path = getattr(test_module, "__file__")
                    if test_module_path:
                        # if we execute the tests using the script mode, the module name is __main__
                        # this is why we retrieve the module name from the path
                        module_name = os.path.splitext(
                            os.path.basename(test_module_path)
                        )[0]
                        label = f"tearDownModule ({module_name})"

                        test_module_path = os.path.relpath(test_module_path)
                        full_label = f"{test_module_path}::tearDownModule"

            with httpdbg_group(records, label, full_label, updatable=False):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


@typing.no_type_check
@contextmanager
def hook_unittest(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import unittest

        unittest.case.TestCase.run = decorate(
            records, unittest.case.TestCase.run, set_hook_for_unittest_run
        )
        unittest.case.TestCase._callSetUp = decorate(
            records, unittest.case.TestCase._callSetUp, set_hook_for_unittest_fixture
        )
        unittest.case.TestCase._callTearDown = decorate(
            records, unittest.case.TestCase._callTearDown, set_hook_for_unittest_fixture
        )
        unittest.suite.TestSuite._handleClassSetUp = decorate(
            records,
            unittest.suite.TestSuite._handleClassSetUp,
            set_hook_for_unittest_class_setup,
        )
        unittest.suite.TestSuite._tearDownPreviousClass = decorate(
            records,
            unittest.suite.TestSuite._tearDownPreviousClass,
            set_hook_for_unittest_class_teardown,
        )
        unittest.suite.TestSuite._handleModuleFixture = decorate(
            records,
            unittest.suite.TestSuite._handleModuleFixture,
            set_hook_for_unittest_module_setup,
        )
        unittest.suite.TestSuite._handleModuleTearDown = decorate(
            records,
            unittest.suite.TestSuite._handleModuleTearDown,
            set_hook_for_unittest_module_teardown,
        )
        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        unittest.case.TestCase.run = undecorate(unittest.case.TestCase.run)
        unittest.case.TestCase._callSetUp = undecorate(
            unittest.case.TestCase._callSetUp
        )
        unittest.case.TestCase._callTearDown = undecorate(
            unittest.case.TestCase._callTearDown
        )
        unittest.suite.TestSuite._handleClassSetUp = undecorate(
            unittest.suite.TestSuite._handleClassSetUp
        )
        unittest.suite.TestSuite._tearDownPreviousClass = undecorate(
            unittest.suite.TestSuite._tearDownPreviousClass
        )
        unittest.suite.TestSuite._handleModuleFixture = undecorate(
            unittest.suite.TestSuite._handleModuleFixture
        )
        unittest.suite.TestSuite._handleModuleTearDown = undecorate(
            unittest.suite.TestSuite._handleModuleTearDown
        )
