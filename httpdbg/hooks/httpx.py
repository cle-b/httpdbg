# -*- coding: utf-8 -*-
from contextlib import contextmanager

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import get_initiator
from httpdbg.records import HTTPRecord


def _record_exception(records, exception, method, *args, **kwargs):
    callargs = getcallargs(method, *args, **kwargs)
    request = callargs.get("request")

    if request:
        if hasattr(request, "url"):
            record = HTTPRecord()

            record.initiator = get_initiator(records._initiators)
            record.url = str(request.url)
            record.exception = exception

            records.requests[record.id] = record


def set_hook_for_httpx(records, method):
    def hook(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as ex:
            _record_exception(records, ex, method, *args, **kwargs)
            raise

    return hook


def set_hook_for_httpx_async(records, method):
    async def hook(*args, **kwargs):
        try:
            return await method(*args, **kwargs)
        except Exception as ex:
            _record_exception(records, ex, method, *args, **kwargs)
            raise

    return hook


@contextmanager
def hook_httpx(records):
    hooks = False
    try:
        import httpx

        httpx._client.Client.send = decorate(
            records, httpx._client.Client.send, set_hook_for_httpx
        )
        httpx._client.AsyncClient.send = decorate(
            records, httpx._client.AsyncClient.send, set_hook_for_httpx_async
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        httpx._client.Client.send = undecorate(httpx._client.Client.send)
        httpx._client.AsyncClient.send = undecorate(httpx._client.AsyncClient.send)
