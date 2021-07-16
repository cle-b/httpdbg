# -*- coding: utf-8 -*-
import pytest
import requests
import vcr

from httpdbg.vcrpy import HTTPDBGPersister

from httpdbg.vcrpy.utils import get_headers, get_header


@pytest.mark.vcrpy
def test_vcrpy_utils_get_headers_request(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/get")
        assert {"name": "Accept", "value": "*/*"} in get_headers(k7.requests[0].headers)


@pytest.mark.vcrpy
def test_vcrpy_utils_get_headers_response(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/get")
        assert {"name": "Content-Type", "value": "application/json"} in get_headers(
            k7.responses[0]["headers"]
        )


@pytest.mark.vcrpy
def test_vcrpy_utils_get_header_request(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/get")
        assert "gzip" in get_header(k7.requests[0].headers, "Accept-Encoding")
        assert "gzip" in get_header(k7.requests[0].headers, "ACCEPT-Encoding")


@pytest.mark.vcrpy
def test_vcrpy_utils_get_header_response(httpbin):

    my_vcr = vcr.VCR(record_mode="all")
    my_vcr.register_persister(HTTPDBGPersister)

    with my_vcr.use_cassette(path="cassettes", decode_compressed_response=True) as k7:
        requests.get(httpbin.url + "/get")
        assert (
            get_header(k7.responses[0]["headers"], "Content-Type") == "application/json"
        )
        assert (
            get_header(k7.responses[0]["headers"], "content-type") == "application/json"
        )
