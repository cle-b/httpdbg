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

            with httpdbg_group(records, label, full_label):
                ret = method(*args, **kwargs)
        else:
            ret = method(*args, **kwargs)
        return ret

    return hook


def set_hook_for_unittest_fixture(_: HTTPRecords, method: Callable):

    def hook(*args, **kwargs):

        if getattr(method, "__name__") == "_callSetUp":
            with httpdbg_tag("setUp"):
                return method(*args, **kwargs)
        elif getattr(method, "__name__") == "_callTearDown":
            with httpdbg_tag("tearDown"):
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

            with httpdbg_group(records, label, full_label):
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

            with httpdbg_group(records, label, full_label):
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
