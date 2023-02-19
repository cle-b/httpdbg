# -*- coding: utf-8 -*-
import inspect

from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp
from httpdbg.utils import logger


def set_hook_for_aiohttp_request_async(records):
    """Intercepts the connection errors"""
    try:
        import aiohttp

        if can_set_hook(
            aiohttp.client.ClientSession, "_request", f"_original_request_{records.id}"
        ):

            async def _hook_request(*args, **kwargs):

                original_method = getattr(
                    aiohttp.client.ClientSession,
                    f"_original_request_{records.id}",
                )
                callargs = inspect.getcallargs(original_method, *args, **kwargs)
                logger.debug(f"aiohttp.client.ClientSession._request - {callargs}")

                method = callargs.get("method")
                str_or_url = callargs.get("str_or_url")

                try:
                    response = await original_method(*args, **kwargs)
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

            async def _hook_send(*args, **kwargs):

                original_method = getattr(
                    aiohttp.client_reqrep.ClientRequest,
                    f"_original_send_{records.id}",
                )
                callargs = inspect.getcallargs(original_method, *args, **kwargs)
                logger.debug(f"aiohttp.client_reqrep.ClientRequest.send - {callargs}")

                request = callargs.get("self")
                url = getattr(request, "url", None)
                method = getattr(request, "method", None)
                headers = getattr(request, "headers", {})
                body = getattr(request, "body", None)
                body = getattr(
                    body, "_value", body
                )  # works even if request.body doesn't exist

                record = HTTPRecord()
                record.initiator = get_initiator(records._initiators)
                record.url = str(url)
                record.method = method
                record.stream = False

                record.request = HTTPRecordContentUp(
                    headers,
                    list_cookies_headers_request_simple_cookies(headers),
                    body,
                )

                records.requests[record.id] = record

                try:
                    response = await original_method(*args, **kwargs)
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

            async def _hook_start(*args, **kwargs):

                original_method = getattr(
                    aiohttp.client_reqrep.ClientResponse,
                    f"_original_start_{records.id}",
                )
                callargs = inspect.getcallargs(original_method, *args, **kwargs)
                logger.debug(
                    "aiohttp.client_reqrep.ClientResponse.start"
                )  # for this hook, str(callargs) can't be called

                self = callargs.get("self")

                record = None

                if hasattr(self, "_httpdbg_record_id"):
                    record = records.requests[self._httpdbg_record_id]

                try:
                    response = await original_method(*args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    headers = getattr(response, "headers", {})
                    reason = getattr(response, "reason", None)
                    status = getattr(response, "status", None)

                    record.response = HTTPRecordContentDown(
                        headers,
                        list_cookies_headers_response_simple_cookies(headers),
                        None,
                    )
                    record._reason = reason
                    record.status_code = status
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

            async def _hook_read(*args, **kwargs):

                original_method = getattr(
                    aiohttp.client_reqrep.ClientResponse,
                    f"_original_read_{records.id}",
                )
                callargs = inspect.getcallargs(original_method, *args, **kwargs)
                logger.debug(f"aiohttp.client_reqrep.ClientResponse.read - {callargs}")

                self = callargs.get("self")

                record = None

                if hasattr(self, "_httpdbg_record_id"):
                    record = records.requests[self._httpdbg_record_id]

                try:
                    content = await original_method(*args, **kwargs)
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
