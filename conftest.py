# -*- coding: utf-8 -*-
import pytest

from httpdbg.webapp import httpdebugk7


@pytest.fixture(autouse=True)
def clear_k7():
    httpdebugk7["k7"] = None
