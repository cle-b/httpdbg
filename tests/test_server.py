# -*- coding: utf-8 -*-
import pytest
import requests

from httpdbg.hooks.all import httprecord


@pytest.mark.cm
def test_httprecord(httpbin_both):
    with httprecord(client=True, server=True) as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 2

    for http_record in records:
        assert http_record.url == f"{httpbin_both.url}/get"
        assert http_record.method.upper() == "GET"
        assert http_record.status_code == 200
        assert http_record.reason.upper() == "OK"

    assert records[0].is_client != records[1].is_client


@pytest.mark.cm
def test_httprecord_client_only(httpbin_both):
    with httprecord() as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1

    http_record = records[0]
    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert records[0].is_client is True


@pytest.mark.cm
def test_httprecord_server_only(httpbin_both):
    with httprecord(client=False, server=True) as records:
        requests.get(f"{httpbin_both.url}/get", verify=False)

    assert len(records) == 1

    http_record = records[0]
    assert http_record.url == f"{httpbin_both.url}/get"
    assert http_record.method.upper() == "GET"
    assert http_record.status_code == 200
    assert http_record.reason.upper() == "OK"
    assert records[0].is_client is False
