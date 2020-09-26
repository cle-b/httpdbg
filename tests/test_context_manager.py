# -*- coding: utf-8 -*-
import requests

import pytest

from httpdbg import httpdbg
from httpdbg.webapp import httpdebugk7

from utils import httpdbg_port


@pytest.mark.cm
def test_context_manager(httpbin):

    assert httpdebugk7["k7"] is None

    requests.get(httpbin.url + "/get")
    assert httpdebugk7["k7"] is None

    with httpdbg(next(httpdbg_port)):
        requests.get(httpbin.url + "/get")
        assert len(httpdebugk7["k7"]) == 1
