# -*- coding: utf-8 -*-
from itertools import count
import os

import niobium  # noqa: F401 - niobium automatically patches selenium
import pytest


@pytest.fixture(scope="session")
def httpdbg_port_base():
    return count(4500)


@pytest.fixture()
def httpdbg_port(httpdbg_port_base):
    return next(httpdbg_port_base)


@pytest.fixture(scope="session")
def httpdbg_host():
    return os.environ.get("HTTPDBG_HOST", "127.0.0.1")
