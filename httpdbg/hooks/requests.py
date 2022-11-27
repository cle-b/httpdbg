# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request
from httpdbg.hooks.cookies import list_cookies_headers_response
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_requests(records):
    """Intercepts the HTTP requests"""
    try:
        import requests

        if not hasattr(requests.adapters.HTTPAdapter, f"_original_send_{records.id}"):

            setattr(
                requests.adapters.HTTPAdapter,
                f"_original_send_{records.id}",
                requests.adapters.HTTPAdapter.send,
            )

            def _hook_send(self, request, *args, **kwargs):

                record = HTTPRecord()

                record.initiator = get_initiator()

                record.url = request.url
                record.method = request.method
                record.stream = kwargs.get("stream", False)
                record.request = HTTPRecordContentUp(
                    request.headers,
                    list_cookies_headers_request(request.headers, request._cookies),
                    request.body,
                )

                records.requests[record.id] = record

                try:
                    response = getattr(
                        requests.adapters.HTTPAdapter, f"_original_send_{records.id}"
                    )(self, request, *args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                record.response = HTTPRecordContentDown(
                    response.headers,
                    list_cookies_headers_response(response.headers, response.cookies),
                    response.content if not record.stream else None,
                )
                record._reason = response.reason
                # change the status_code at the end to be sure the ui reload a fresh description of the request
                record.status_code = response.status_code

                return response

            requests.adapters.HTTPAdapter.send = _hook_send
    except ImportError:
        pass


def unset_hook_for_requests(records):
    try:
        import requests

        if hasattr(requests.adapters.HTTPAdapter, f"_original_send_{records.id}"):
            requests.adapters.HTTPAdapter.send = getattr(
                requests.adapters.HTTPAdapter, f"_original_send_{records.id}"
            )
            delattr(requests.adapters.HTTPAdapter, f"_original_send_{records.id}")
    except ImportError:
        pass
