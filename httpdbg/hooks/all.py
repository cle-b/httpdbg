# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
from typing import List
from typing import Union

from httpdbg.hooks.aiohttp import hook_aiohttp
from httpdbg.hooks.external import watcher_external
from httpdbg.hooks.generic import hook_generic
from httpdbg.hooks.httpx import hook_httpx
from httpdbg.hooks.pytest import hook_pytest
from httpdbg.hooks.requests import hook_requests
from httpdbg.hooks.socket import hook_socket
from httpdbg.hooks.urllib3 import hook_urllib3
from httpdbg.records import HTTPRecords


@contextmanager
def httprecord(
    records: HTTPRecords = None, initiators: Union[List[str], None] = None
) -> Generator[HTTPRecords, None, None]:
    if records is None:
        records = HTTPRecords()

    with watcher_external(records):
        with hook_socket(records):
            with hook_httpx(records):
                with hook_requests(records):
                    with hook_urllib3(records):
                        with hook_aiohttp(records):
                            with hook_pytest(records):
                                with hook_generic(records, initiators):
                                    yield records
