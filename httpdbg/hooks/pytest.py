# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_tag
from httpdbg.records import HTTPRecords


def set_hook_for_pytest_fixture(_, method):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        if "fixturefunc" in callargs:
            with httpdbg_tag(getattr(callargs["fixturefunc"], "__name__", "fixture")):
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return hook


@contextmanager
def hook_pytest(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import _pytest.fixtures

        _pytest.fixtures.call_fixture_func = decorate(
            records, _pytest.fixtures.call_fixture_func, set_hook_for_pytest_fixture
        )
        _pytest.fixtures._teardown_yield_fixture = decorate(
            records,
            _pytest.fixtures._teardown_yield_fixture,
            set_hook_for_pytest_fixture,
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
