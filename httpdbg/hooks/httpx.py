# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_response
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp
from httpdbg.hooks.utils import getcallargs


def set_hook_for_httpx_send(records):
    """Intercepts the HTTP requests"""
    try:
        import httpx

        set_hook, original_method = can_set_hook(
            httpx._client.Client, "send", f"_original_send_{records.id}"
        )

        if set_hook:

            def _hook_send(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = HTTPRecord()
                record.initiator = get_initiator(records._initiators)

                request = callargs.get("request")
                record.url = str(getattr(request, "url", ""))
                record.method = getattr(request, "method", None)
                record.stream = callargs.get("stream", False)

                headers = getattr(request, "headers", {})
                cookies = getattr(request, "_httpdbg_cookies", [])
                cookies_jar = getattr(cookies, "jar", [])
                record.request = HTTPRecordContentUp(
                    headers,
                    list_cookies_headers_response(headers, cookies_jar),
                    getattr(request, "content", None) if not record.stream else None,
                )

                records.requests[record.id] = record

                try:
                    response = original_method(*args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                headers = getattr(response, "headers", {})
                cookies = getattr(response, "cookies", [])
                cookies_jar = getattr(cookies, "jar", [])
                record.response = HTTPRecordContentDown(
                    headers,
                    list_cookies_headers_response(headers, cookies_jar),
                    getattr(response, "content", None),
                )
                record._reason = getattr(response, "reason_phrase", None)
                record.status_code = getattr(response, "status_code", None)

                return response

            httpx._client.Client.send = _hook_send
    except ImportError:
        pass


def unset_hook_for_httpx_send(records):
    try:
        import httpx

        unset_hook(
            httpx._client.Client,
            "send",
            f"_original_send_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpx_send_async(records):
    """Intercepts the HTTP requests"""
    try:
        import httpx

        set_hook, original_method = can_set_hook(
            httpx._client.AsyncClient, "send", f"_original_send_{records.id}"
        )

        if set_hook:

            async def _hook_send(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = HTTPRecord()
                record.initiator = get_initiator(records._initiators)

                request = callargs.get("request")
                record.url = str(getattr(request, "url", ""))
                record.method = getattr(request, "method", None)
                record.stream = callargs.get("stream", False)

                headers = getattr(request, "headers", {})
                cookies = getattr(request, "_httpdbg_cookies", [])
                cookies_jar = getattr(cookies, "jar", [])
                record.request = HTTPRecordContentUp(
                    headers,
                    list_cookies_headers_response(headers, cookies_jar),
                    getattr(request, "content", None),
                )

                records.requests[record.id] = record

                try:
                    response = await original_method(*args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                headers = getattr(response, "headers", {})
                cookies = getattr(response, "cookies", [])
                cookies_jar = getattr(cookies, "jar", [])
                record.response = HTTPRecordContentDown(
                    headers,
                    list_cookies_headers_response(headers, cookies_jar),
                    getattr(response, "content", None) if not record.stream else None,
                )
                record._reason = getattr(response, "reason_phrase", None)
                record.status_code = getattr(response, "status_code", None)

                return response

            httpx._client.AsyncClient.send = _hook_send
    except ImportError:
        pass


def unset_hook_for_httpx_send_async(records):
    try:
        import httpx

        unset_hook(
            httpx._client.AsyncClient,
            "send",
            f"_original_send_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpx_request(records):
    try:
        import httpx

        set_hook, original_method = can_set_hook(
            httpx._models.Request, "__init__", f"_original_init_{records.id}"
        )

        if set_hook:

            def _hook_init(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                self = callargs.get("self")

                self._httpdbg_cookies = kwargs.get("cookies")

                original_method(*args, **kwargs)

            httpx._models.Request.__init__ = _hook_init
    except ImportError:
        pass


def unset_hook_for_httpx_request(records):
    try:
        import httpx

        unset_hook(
            httpx._models.Request,
            "__init__",
            f"_original_init_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpx(records):
    set_hook_for_httpx_send(records)
    set_hook_for_httpx_send_async(records)
    set_hook_for_httpx_request(records)


def unset_hook_for_httpx(records):
    unset_hook_for_httpx_send(records)
    unset_hook_for_httpx_send_async(records)
    unset_hook_for_httpx_request(records)
