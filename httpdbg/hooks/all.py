# -*- coding: utf-8 -*-
from contextlib import contextmanager

from httpdbg.hooks.aiohttp import hook_aiohttp
from httpdbg.hooks.httpx import hook_httpx
from httpdbg.hooks.requests import hook_requests
from httpdbg.hooks.socket import hook_socket
from httpdbg.hooks.urllib3 import hook_urllib3
from httpdbg.records import HTTPRecords


@contextmanager
def httpdbg(records=None):
    if records is None:
        records = HTTPRecords()

    with hook_socket(records):
        with hook_httpx(records):
            with hook_requests(records):
                with hook_urllib3(records):
                    with hook_aiohttp(records):
                        yield records
