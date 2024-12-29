# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
from typing import Generator

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_group
from httpdbg.initiator import httpdbg_tag
from httpdbg.log import logger
from httpdbg.records import HTTPRecords


def set_hook_for_pytest_fixture(_: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        logger().info("SET_HOOK_FOR_PYTEST_FIXTURE")
        callargs = getcallargs(method, *args, **kwargs)

        if "fixturefunc" in callargs:
            with httpdbg_tag(getattr(callargs["fixturefunc"], "__name__", "fixture")):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


def set_hook_for_pytest_runtest(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        logger().info("SET_HOOK_FOR_PYTEST_RUNTEST")
        callargs = getcallargs(method, *args, **kwargs)

        if "item" in callargs:
            full_label = getattr(callargs["item"], "nodeid", "unknown test")
            label = getattr(callargs["item"], "name", "unknown test")
            with httpdbg_group(records, label, full_label):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


@contextmanager
def hook_pytest(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import _pytest.fixtures
        import _pytest.runner

        _pytest.fixtures.call_fixture_func = decorate(
            records, _pytest.fixtures.call_fixture_func, set_hook_for_pytest_fixture
        )
        _pytest.fixtures._teardown_yield_fixture = decorate(
            records,
            _pytest.fixtures._teardown_yield_fixture,
            set_hook_for_pytest_fixture,
        )

        _pytest.runner.runtestprotocol = decorate(
            records, _pytest.runner.runtestprotocol, set_hook_for_pytest_runtest
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        _pytest.fixtures.call_fixture_func = undecorate(
            _pytest.fixtures.call_fixture_func
        )
        _pytest.fixtures._teardown_yield_fixture = undecorate(
            _pytest.fixtures._teardown_yield_fixture
        )

        _pytest.runner.runtestprotocol = undecorate(_pytest.runner.runtestprotocol)
