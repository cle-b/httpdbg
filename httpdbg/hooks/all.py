# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
from typing import List
from typing import Tuple
from typing import Union

from httpdbg.hooks.aiohttp import hook_aiohttp
from httpdbg.hooks.external import watcher_external
from httpdbg.hooks.generic import hook_generic
from httpdbg.hooks.http import hook_http
from httpdbg.hooks.httpx import hook_httpx
from httpdbg.hooks.pytest import hook_pytest
from httpdbg.hooks.requests import hook_requests
from httpdbg.hooks.socket import hook_socket
from httpdbg.hooks.unittest import hook_unittest
from httpdbg.hooks.urllib3 import hook_urllib3
from httpdbg.hooks.flask import hook_flask
from httpdbg.records import HTTPRecords


@contextmanager
def httprecord(
    records: HTTPRecords = None,
    initiators: Union[List[str], None] = None,
    client: bool = True,
    server: bool = False,
    ignore: Union[List[Tuple[str, int]], None] = None,
) -> Generator[HTTPRecords, None, None]:
    if records is None:
        records = HTTPRecords(client=client, server=server, ignore=ignore)

    with watcher_external(records, initiators, server):
        with hook_flask(records):
            with hook_socket(records):
                with hook_http(records):
                    with hook_httpx(records):
                        with hook_requests(records):
                            with hook_urllib3(records):
                                with hook_aiohttp(records):
                                    with hook_pytest(records):
                                        with hook_unittest(records):
                                            with hook_generic(records, initiators):
                                                yield records
