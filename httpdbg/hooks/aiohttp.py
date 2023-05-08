# -*- coding: utf-8 -*-
from contextlib import contextmanager
import traceback
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecords


def set_hook_for_aiohttp_async(records, method):
    async def hook(*args, **kwargs):
        initiator = None
        try:
            with httpdbg_initiator(
                records, traceback.extract_stack(), method, *args, **kwargs
            ) as initiator:
                ret = await method(*args, **kwargs)
            return ret
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)

            if "str_or_url" in callargs:
                if initiator:
                    record = HTTPRecord()

                    record.initiator = initiator
                    record.url = str(callargs["str_or_url"])
                    record.exception = ex

                    records.requests[record.id] = record
            raise

    return hook


@contextmanager
def hook_aiohttp(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import aiohttp

        aiohttp.ClientSession._request = decorate(
            records, aiohttp.ClientSession._request, set_hook_for_aiohttp_async
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        aiohttp.ClientSession._request = undecorate(aiohttp.ClientSession._request)
