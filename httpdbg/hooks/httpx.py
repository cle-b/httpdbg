# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_response
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_httpx_send(records):
    """Intercepts the HTTP requests"""
    try:
        import httpx

        if can_set_hook(httpx._client.Client, "send", f"_original_send_{records.id}"):

            def _hook_send(self, request, *args, **kwargs):

                record = HTTPRecord()

                record.initiator = get_initiator(records._initiators)

                record.url = str(request.url)
                record.method = request.method
                record.stream = kwargs.get("stream", False)

                record.request = HTTPRecordContentUp(
                    request.headers,
                    list_cookies_headers_response(
                        request.headers, request._httpdbg_cookies.jar
                    )
                    if request._httpdbg_cookies
                    else [],
                    request.content if not record.stream else None,
                )

                records.requests[record.id] = record

                try:
                    response = getattr(
                        httpx._client.Client, f"_original_send_{records.id}"
                    )(self, request, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                record.response = HTTPRecordContentDown(
                    response.headers,
                    list_cookies_headers_response(
                        response.headers, response.cookies.jar
                    ),
                    response.content,
                )
                record._reason = response.reason_phrase
                record.status_code = response.status_code

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

        if can_set_hook(
            httpx._client.AsyncClient, "send", f"_original_send_{records.id}"
        ):

            async def _hook_send(self, request, *args, **kwargs):

                record = HTTPRecord()

                record.initiator = get_initiator(records._initiators)

                record.url = str(request.url)
                record.method = request.method
                record.stream = kwargs.get("stream", False)

                record.request = HTTPRecordContentUp(
                    request.headers,
                    list_cookies_headers_response(
                        request.headers, request._httpdbg_cookies.jar
                    )
                    if request._httpdbg_cookies
                    else [],
                    request.content if not record.stream else None,
                )

                records.requests[record.id] = record

                try:
                    response = await getattr(
                        httpx._client.AsyncClient, f"_original_send_{records.id}"
                    )(self, request, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                record.response = HTTPRecordContentDown(
                    response.headers,
                    list_cookies_headers_response(
                        response.headers, response.cookies.jar
                    ),
                    response.content if not record.stream else None,
                )
                record._reason = response.reason_phrase
                record.status_code = response.status_code

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

        if can_set_hook(
            httpx._models.Request, "__init__", f"_original_init_{records.id}"
        ):

            def _hook_init(self, *args, **kwargs):

                self._httpdbg_cookies = kwargs.get("cookies")

                getattr(httpx._models.Request, f"_original_init_{records.id}")(
                    self, *args, **kwargs
                )

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
