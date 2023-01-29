# -*- coding: utf-8 -*-
import random

import pytest
import requests

from httpdbg.server import httpdbg
from httpdbg.server import httpdbg_srv
from tests.web.ui import HttpdbgWebUI


@pytest.fixture()
def records(httpbin, httpdbg_port):
    with httpdbg_srv(httpdbg_port) as records:
        with httpdbg(records):
            for n in range(2, random.randint(5, 8)):
                requests.get(httpbin.url + f"/get?n={n}")

        yield records


@pytest.fixture()
def httpdbgui(selenium, httpdbg_host, httpdbg_port, records):
    selenium.implicitly_wait(5)
    yield HttpdbgWebUI(f"http://{httpdbg_host}:{httpdbg_port}", selenium)


@pytest.mark.ui
def test_ui_list_records(httpdbgui, records):

    assert len(records) == len(httpdbgui.requests)

    for record in records:
        assert record.id in httpdbgui.requests

    record = records[2]
    ui_request = httpdbgui.requests[record.id]
    assert str(record.status_code) == ui_request.status
    assert record.method == ui_request.method
    assert record.url == ui_request.url
