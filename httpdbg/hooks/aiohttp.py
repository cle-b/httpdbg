# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_aiohttp_send_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if not hasattr(
            aiohttp.client_reqrep.ClientRequest, f"_original_send_{records.id}"
        ):

            setattr(
                aiohttp.client_reqrep.ClientRequest,
                f"_original_send_{records.id}",
                aiohttp.client_reqrep.ClientRequest.send,
            )

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

        if hasattr(aiohttp.client_reqrep.ClientRequest, f"_original_send_{records.id}"):
            aiohttp.client_reqrep.ClientRequest.send = getattr(
                aiohttp.client_reqrep.ClientRequest, f"_original_send_{records.id}"
            )
            delattr(aiohttp.client_reqrep.ClientRequest, f"_original_send_{records.id}")
    except ImportError:
        pass


def set_hook_for_aiohttp_start_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if not hasattr(
            aiohttp.client_reqrep.ClientResponse, f"_original_start_{records.id}"
        ):

            setattr(
                aiohttp.client_reqrep.ClientResponse,
                f"_original_start_{records.id}",
                aiohttp.client_reqrep.ClientResponse.start,
            )

            async def _hook_start(self, *args, **kwargs):

                reponse = self

                record = records.requests[reponse._httpdbg_record_id]

                try:
                    response = await getattr(
                        aiohttp.client_reqrep.ClientResponse,
                        f"_original_start_{records.id}",
                    )(self, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

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

        if hasattr(
            aiohttp.client_reqrep.ClientResponse, f"_original_start_{records.id}"
        ):
            aiohttp.client_reqrep.ClientResponse.start = getattr(
                aiohttp.client_reqrep.ClientResponse, f"_original_start_{records.id}"
            )
            delattr(
                aiohttp.client_reqrep.ClientResponse, f"_original_start_{records.id}"
            )
    except ImportError:
        pass


def set_hook_for_aiohttp_read_async(records):
    """Intercepts the HTTP requests"""
    try:
        import aiohttp

        if not hasattr(
            aiohttp.client_reqrep.ClientResponse, f"_original_read_{records.id}"
        ):

            setattr(
                aiohttp.client_reqrep.ClientResponse,
                f"_original_read_{records.id}",
                aiohttp.client_reqrep.ClientResponse.read,
            )

            async def _hook_read(self, *args, **kwargs):

                reponse = self

                record = records.requests[reponse._httpdbg_record_id]

                try:
                    content = await getattr(
                        aiohttp.client_reqrep.ClientResponse,
                        f"_original_read_{records.id}",
                    )(self, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                record.response.content = content

                return content

            aiohttp.client_reqrep.ClientResponse.read = _hook_read
    except ImportError:
        pass


def unset_hook_for_aiohttp_read_async(records):
    try:
        import aiohttp

        if hasattr(
            aiohttp.client_reqrep.ClientResponse, f"_original_read_{records.id}"
        ):
            aiohttp.client_reqrep.ClientResponse.read = getattr(
                aiohttp.client_reqrep.ClientResponse, f"_original_read_{records.id}"
            )
            delattr(
                aiohttp.client_reqrep.ClientResponse, f"_original_read_{records.id}"
            )
    except ImportError:
        pass


def set_hook_for_aiohttp(records):
    set_hook_for_aiohttp_send_async(records)
    set_hook_for_aiohttp_start_async(records)
    set_hook_for_aiohttp_read_async(records)


def unset_hook_for_aiohttp(records):
    unset_hook_for_aiohttp_send_async(records)
    unset_hook_for_aiohttp_start_async(records)
    unset_hook_for_aiohttp_read_async(records)
