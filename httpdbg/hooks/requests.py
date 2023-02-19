# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request
from httpdbg.hooks.cookies import list_cookies_headers_response
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp
from httpdbg.hooks.utils import getcallargs


def set_hook_for_requests(records):
    """Intercepts the HTTP requests"""
    try:
        import requests

        set_hook, original_method = can_set_hook(
            requests.adapters.HTTPAdapter, "send", f"_original_send_{records.id}"
        )

        if set_hook:

            def _hook_send(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = HTTPRecord()
                record.initiator = get_initiator(records._initiators)

                request = callargs.get("request")

                record.url = getattr(request, "url", "")
                record.method = getattr(request, "method", None)
                record.stream = callargs.get("stream", False)

                headers = getattr(request, "headers", {})
                record.request = HTTPRecordContentUp(
                    headers,
                    list_cookies_headers_request(
                        headers, getattr(request, "_cookies", {})
                    ),
                    getattr(request, "body", None),
                )

                records.requests[record.id] = record

                try:
                    response = original_method(*args, **kwargs)
                except Exception as ex:
                    record.exception = ex
                    record.status_code = -1
                    raise

                headers = getattr(response, "headers", {})
                record.response = HTTPRecordContentDown(
                    headers,
                    list_cookies_headers_response(
                        headers, cookies=getattr(response, "cookies", None)
                    ),
                    getattr(response, "content", None) if not record.stream else None,
                )
                record._reason = getattr(response, "reason", None)
                record.status_code = getattr(response, "status_code", None)

                return response

            requests.adapters.HTTPAdapter.send = _hook_send
    except ImportError:
        pass


def unset_hook_for_requests(records):
    try:
        import requests

        unset_hook(
            requests.adapters.HTTPAdapter,
            "send",
            f"_original_send_{records.id}",
        )
    except ImportError:
        pass
