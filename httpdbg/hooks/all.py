# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
from typing import List
from typing import Union

from httpdbg.hooks.aiohttp import hook_aiohttp
from httpdbg.hooks.generic import hook_generic
from httpdbg.hooks.httpx import hook_httpx
from httpdbg.hooks.requests import hook_requests
from httpdbg.hooks.socket import hook_socket
from httpdbg.hooks.urllib3 import hook_urllib3
from httpdbg.records import HTTPRecords


@contextmanager
def httpdbg(
    records: HTTPRecords = None, initiators: Union[List[str], None] = None
) -> Generator[HTTPRecords, None, None]:
    if records is None:
        records = HTTPRecords()

    with hook_socket(records):
        with hook_httpx(records):
            with hook_requests(records):
                with hook_urllib3(records):
                    with hook_aiohttp(records):
                        with hook_generic(records, initiators):
                            yield records
