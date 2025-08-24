from contextlib import contextmanager
from typing import Generator
from typing import Union

from httpdbg.hooks.aiohttp import hook_aiohttp
from httpdbg.hooks.external import watcher_external
from httpdbg.hooks.fastapi import hook_fastapi
from httpdbg.hooks.flask import hook_flask
from httpdbg.hooks.generic import hook_generic
from httpdbg.hooks.h2 import hook_h2
from httpdbg.hooks.http import hook_http
from httpdbg.hooks.httpx import hook_httpx
from httpdbg.hooks.pytest import hook_pytest
from httpdbg.hooks.requests import hook_requests
from httpdbg.hooks.socket import hook_socket
from httpdbg.hooks.starlette import hook_starlette
from httpdbg.hooks.unittest import hook_unittest
from httpdbg.hooks.urllib3 import hook_urllib3
from httpdbg.hooks.uvicorn import hook_uvicorn

from httpdbg.records import HTTPRecords


@contextmanager
def httprecord(
    records: HTTPRecords = None,
    initiators: Union[list[str], None] = None,
    client: bool = True,
    server: bool = False,
    ignore: tuple[tuple[str, int], ...] = (),
    multiprocess: bool = True,
) -> Generator[HTTPRecords, None, None]:
    if records is None:
        records = HTTPRecords(client=client, server=server, ignore=ignore)

    with hook_flask(records):
        with hook_socket(records):
            with hook_h2(records):
                with hook_fastapi(records):
                    with hook_starlette(records):
                        with hook_uvicorn(records):
                            with hook_http(records):
                                with hook_httpx(records):
                                    with hook_requests(records):
                                        with hook_urllib3(records):
                                            with hook_aiohttp(records):
                                                with hook_pytest(records):
                                                    with hook_unittest(records):
                                                        with hook_generic(
                                                            records, initiators
                                                        ):
                                                            if multiprocess:
                                                                with watcher_external(
                                                                    records,
                                                                    initiators,
                                                                    server,
                                                                ):
                                                                    yield records
                                                            else:
                                                                yield records
