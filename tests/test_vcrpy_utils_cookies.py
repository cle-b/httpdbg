# -*- coding: utf-8 -*-
import pytest
import requests
import vcr

from httpdbg.vcrpy import HTTPDBGPersister

from httpdbg.vcrpy.utils import list_cookies_request, list_cookies_response


@pytest.mark.vcrpy
def test_vcrpy_utils_list_cookies_request(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/get", cookies={"c1": "v1", "c2": "v2"})

        assert list_cookies_request(k7.requests[0].headers) == [
            {"name": "c1", "value": "v1"},
            {"name": "c2", "value": "v2"},
        ]


@pytest.mark.vcrpy
def test_vcrpy_utils_list_cookies_response(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/cookies/set?cc1=vv1&cc2=vv2")
        cookies = list_cookies_response(k7.responses[0]["headers"])

        assert len(cookies) == 2

        assert cookies[0]["name"] == "cc1"
        assert cookies[0]["value"] == "vv1"
        assert {"name": "expires", "value": ""} in cookies[0]["attributes"]

        assert cookies[1]["name"] == "cc2"
        assert cookies[1]["value"] == "vv2"
