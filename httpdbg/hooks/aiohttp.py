# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_aiohttp_request_async(records):
    """Intercepts the connection errors"""
    try:
        import aiohttp

        if can_set_hook(
            aiohttp.client.ClientSession, "_request", f"_original_request_{records.id}"
        ):

            async def _hook_request(self, method, str_or_url, *args, **kwargs):

                try:
                    response = await getattr(
                        aiohttp.client.ClientSession,
                        f"_original_request_{records.id}",
                    )(self, method, str_or_url, *args, **kwargs)
                except Exception as ex:
                    # the request is recorded here only in case of exception
                    record = HTTPRecord()

                    record.initiator = get_initiator(records._initiators)

                    record.url = str(str_or_url)
                    record.method = method
                    record.stream = False

                    record.exception = ex
                    record.status_code = -1

                    records.requests[record.id] = record
                    raise

                return response

            aiohttp.client.ClientSession._request = _hook_request
    except ImportError:
        pass


def unset_hook_for_aiohttp_request_async(records):
    try:
        import aiohttp

        unset_hook(
            aiohttp.client.ClientSession,
            "_request",
            f"_original_request_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_aiohttp_send_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if can_set_hook(
            aiohttp.client_reqrep.ClientRequest, "send", f"_original_send_{records.id}"
        ):

            async def _hook_send(self, *args, **kwargs):

                request = self

                record = HTTPRecord()

                record.initiator = get_initiator(records._initiators)

                record.url = str(request.url)
                record.method = request.method
                record.stream = False

                record.request = HTTPRecordContentUp(
                    request.headers,
                    list_cookies_headers_request_simple_cookies(request.headers),
                    request.body._value
                    if hasattr(request.body, "_value")
                    else request.body,
                )

                records.requests[record.id] = record

                try:
                    response = await getattr(
                        aiohttp.client_reqrep.ClientRequest,
                        f"_original_send_{records.id}",
                    )(self, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                response._httpdbg_record_id = record.id

                return response

            aiohttp.client_reqrep.ClientRequest.send = _hook_send
    except ImportError:
        pass


def unset_hook_for_aiohttp_send_async(records):
    try:
        import aiohttp

        unset_hook(
            aiohttp.client_reqrep.ClientRequest,
            "send",
            f"_original_send_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_aiohttp_start_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if can_set_hook(
            aiohttp.client_reqrep.ClientResponse,
            "start",
            f"_original_start_{records.id}",
        ):

            async def _hook_start(self, *args, **kwargs):

                record = None

                if hasattr(self, "_httpdbg_record_id"):
                    record = records.requests[self._httpdbg_record_id]

                try:
                    response = await getattr(
                        aiohttp.client_reqrep.ClientResponse,
                        f"_original_start_{records.id}",
                    )(self, *args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    record.response = HTTPRecordContentDown(
                        response.headers,
                        list_cookies_headers_response_simple_cookies(response.headers),
                        None,
                    )
                    record._reason = response.reason
                    record.status_code = response.status
                return response

            aiohttp.client_reqrep.ClientResponse.start = _hook_start
    except ImportError:
        pass


def unset_hook_for_aiohttp_start_async(records):
    try:
        import aiohttp

        unset_hook(
            aiohttp.client_reqrep.ClientResponse,
            "start",
            f"_original_start_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_aiohttp_read_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if can_set_hook(
            aiohttp.client_reqrep.ClientResponse, "read", f"_original_read_{records.id}"
        ):

            async def _hook_read(self, *args, **kwargs):

                record = None

                if hasattr(self, "_httpdbg_record_id"):
                    record = records.requests[self._httpdbg_record_id]

                try:
                    content = await getattr(
                        aiohttp.client_reqrep.ClientResponse,
                        f"_original_read_{records.id}",
                    )(self, *args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    record.response.content = content

                return content

            aiohttp.client_reqrep.ClientResponse.read = _hook_read
    except ImportError:
        pass


def unset_hook_for_aiohttp_read_async(records):
    try:
        import aiohttp

        unset_hook(
            aiohttp.client_reqrep.ClientResponse,
            "read",
            f"_original_read_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_aiohttp(records):
    set_hook_for_aiohttp_request_async(records)
    set_hook_for_aiohttp_send_async(records)
    set_hook_for_aiohttp_start_async(records)
    set_hook_for_aiohttp_read_async(records)


def unset_hook_for_aiohttp(records):
    unset_hook_for_aiohttp_request_async(records)
    unset_hook_for_aiohttp_send_async(records)
    unset_hook_for_aiohttp_start_async(records)
    unset_hook_for_aiohttp_read_async(records)
