# -*- coding: utf-8 -*-
from contextlib import contextmanager

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import get_initiator
from httpdbg.records import HTTPRecord


def set_hook_for_aiohttp_async(records, method):
    async def hook(*args, **kwargs):
        try:
            return await method(*args, **kwargs)
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)

            url = str(callargs.get("str_or_url", ""))

            if url:
                record = HTTPRecord()

                record.initiator = get_initiator(records._initiators)
                record.url = url
                record.exception = ex

                records.requests[record.id] = record

            raise

    return hook


@contextmanager
def hook_aiohttp(records):
    hooks = False
    try:
        import aiohttp

        aiohttp.client.ClientSession._request = decorate(
            records, aiohttp.client.ClientSession._request, set_hook_for_aiohttp_async
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        aiohttp.client.ClientSession._request = undecorate(
            aiohttp.client.ClientSession._request
        )
