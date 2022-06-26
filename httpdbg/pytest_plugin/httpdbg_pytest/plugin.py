# -*- coding: utf-8 -*-
import os
import pytest

from httpdbg.source import Source
from httpdbg.webapp import httpdebugk7


# this solution doesn't work if the tests are executed in parallel
# but it's enough for a first version
@pytest.fixture(autouse=True, scope="function")
def link_requests_to_tests():
    """pytest plugin for httpdbg"""
    yield

    src = Source(" ".join(os.environ["PYTEST_CURRENT_TEST"].split(" ")[:-1]))

    for _, req in httpdebugk7.requests.items():
        if req.src is None:
            req.src = src
