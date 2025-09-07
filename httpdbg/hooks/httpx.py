from collections.abc import Callable
from contextlib import contextmanager
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecords


def set_hook_for_httpx_async(records: HTTPRecords, method: Callable):
    async def hook(*args, **kwargs):
        initiator_and_group = None
        try:
            with httpdbg_initiator(
                records, method, *args, **kwargs
            ) as initiator_and_group:
                ret = await method(*args, **kwargs)
            return ret
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)

            if "url" in callargs:
                if initiator_and_group:
                    initiator, group, is_new = initiator_and_group
                    if is_new:
                        records.add_new_record_exception(
                            initiator, group, str(callargs["url"]), ex
                        )
            raise

    return hook


def set_hook_for_httpx(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        initiator_and_group = None
        try:
            with httpdbg_initiator(
                records, method, *args, **kwargs
            ) as initiator_and_group:
                ret = method(*args, **kwargs)
            return ret
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)

            if "url" in callargs:
                if initiator_and_group:
                    initiator, group, is_new = initiator_and_group
                    if is_new:
                        records.add_new_record_exception(
                            initiator, group, str(callargs["url"]), ex
                        )
            raise

    return hook


@contextmanager
def hook_httpx(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import httpx

        httpx.AsyncClient.get = decorate(
            records, httpx.AsyncClient.get, set_hook_for_httpx_async
        )
        httpx.AsyncClient.post = decorate(
            records, httpx.AsyncClient.post, set_hook_for_httpx_async
        )
        httpx.AsyncClient.patch = decorate(
            records, httpx.AsyncClient.patch, set_hook_for_httpx_async
        )
        httpx.AsyncClient.put = decorate(
            records, httpx.AsyncClient.put, set_hook_for_httpx_async
        )
        httpx.AsyncClient.delete = decorate(
            records, httpx.AsyncClient.delete, set_hook_for_httpx_async
        )
        httpx.AsyncClient.head = decorate(
            records, httpx.AsyncClient.head, set_hook_for_httpx_async
        )
        httpx.AsyncClient.options = decorate(
            records, httpx.AsyncClient.options, set_hook_for_httpx_async
        )
        httpx.AsyncClient.request = decorate(
            records, httpx.AsyncClient.request, set_hook_for_httpx_async
        )

        httpx.Client.get = decorate(records, httpx.Client.get, set_hook_for_httpx)
        httpx.Client.post = decorate(records, httpx.Client.post, set_hook_for_httpx)
        httpx.Client.patch = decorate(records, httpx.Client.patch, set_hook_for_httpx)
        httpx.Client.put = decorate(records, httpx.Client.put, set_hook_for_httpx)
        httpx.Client.delete = decorate(records, httpx.Client.delete, set_hook_for_httpx)
        httpx.Client.head = decorate(records, httpx.Client.head, set_hook_for_httpx)
        httpx.Client.options = decorate(
            records, httpx.Client.options, set_hook_for_httpx
        )
        httpx.Client.request = decorate(
            records, httpx.Client.request, set_hook_for_httpx
        )

        httpx.get = decorate(records, httpx.get, set_hook_for_httpx)
        httpx.post = decorate(records, httpx.post, set_hook_for_httpx)
        httpx.patch = decorate(records, httpx.patch, set_hook_for_httpx)
        httpx.put = decorate(records, httpx.put, set_hook_for_httpx)
        httpx.delete = decorate(records, httpx.delete, set_hook_for_httpx)
        httpx.head = decorate(records, httpx.head, set_hook_for_httpx)
        httpx.options = decorate(records, httpx.options, set_hook_for_httpx)
        httpx.request = decorate(records, httpx.request, set_hook_for_httpx)

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        httpx.AsyncClient.get = undecorate(httpx.AsyncClient.get)
        httpx.AsyncClient.post = undecorate(httpx.AsyncClient.post)
        httpx.AsyncClient.patch = undecorate(httpx.AsyncClient.patch)
        httpx.AsyncClient.put = undecorate(httpx.AsyncClient.put)
        httpx.AsyncClient.delete = undecorate(httpx.AsyncClient.delete)
        httpx.AsyncClient.head = undecorate(httpx.AsyncClient.head)
        httpx.AsyncClient.options = undecorate(httpx.AsyncClient.options)
        httpx.AsyncClient.request = undecorate(httpx.AsyncClient.request)

        httpx.Client.get = undecorate(httpx.Client.get)
        httpx.Client.post = undecorate(httpx.Client.post)
        httpx.Client.patch = undecorate(httpx.Client.patch)
        httpx.Client.put = undecorate(httpx.Client.put)
        httpx.Client.delete = undecorate(httpx.Client.delete)
        httpx.Client.head = undecorate(httpx.Client.head)
        httpx.Client.options = undecorate(httpx.Client.options)
        httpx.Client.request = undecorate(httpx.Client.request)

        httpx.get = undecorate(httpx.get)
        httpx.post = undecorate(httpx.post)
        httpx.patch = undecorate(httpx.patch)
        httpx.put = undecorate(httpx.put)
        httpx.delete = undecorate(httpx.delete)
        httpx.head = undecorate(httpx.head)
        httpx.options = undecorate(httpx.options)
        httpx.request = undecorate(httpx.request)
