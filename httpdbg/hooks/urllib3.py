# -*- coding: utf-8 -*-
import os
import traceback

from httpdbg.initiator import get_initiator
from httpdbg.initiator import in_lib
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp
from httpdbg.hooks.utils import getcallargs


def set_hook_for_urllib3_urlopen(records):
    """Intercepts the HTTP requests"""
    try:
        import urllib3

        set_hook, original_method = can_set_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "urlopen",
            f"_httpdbg_original_urlopen_{records.id}",
        )

        if set_hook:

            def _hook_urlopen(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = None

                if record_request():
                    record = HTTPRecord()
                    record.initiator = get_initiator(records._initiators)

                    self = callargs.get("self")
                    port = getattr(self, "port", 0)
                    scheme = getattr(self, "scheme", "")
                    port = (
                        f":{port}"
                        if not (
                            ((scheme.upper() == "HTTP") and port == 80)
                            or ((scheme.upper() == "HTTPS") and port == 443)
                        )
                        else ""
                    )
                    host = getattr(self, "host", "")
                    url = callargs.get("url")
                    record.url = f"{scheme}://{host}{port}{url}"
                    record.method = callargs.get("method")
                    record.stream = False

                    self._httpdbg_record_id = record.id

                    records.requests[record.id] = record

                try:
                    response = original_method(*args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    headers = getattr(response, "headers", {})
                    record.response = HTTPRecordContentDown(
                        headers,
                        list_cookies_headers_response_simple_cookies(headers),
                        getattr(response, "_body", {}),
                    )

                    record._reason = getattr(response, "reason", None)
                    record.status_code = getattr(response, "status", None)

                    response._httpdbg_record_id = record.id

                return response

            urllib3.connectionpool.HTTPConnectionPool.urlopen = _hook_urlopen
    except ImportError:
        pass


def unset_hook_for_urllib3_urlopen(records):
    try:
        import urllib3

        unset_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "urlopen",
            f"_httpdbg_original_urlopen_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_urllib3_make_request(records):
    """Intercepts the HTTP requests"""
    try:
        import urllib3

        set_hook, original_method = can_set_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "_make_request",
            f"_httpdbg_original_make_request_{records.id}",
        )

        if set_hook:

            def _hook_make_request(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = None

                if record_request():
                    self = callargs.get("self")
                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                    headers = callargs.get("headers", {})
                    record.request = HTTPRecordContentUp(
                        headers,
                        list_cookies_headers_request_simple_cookies(headers),
                        callargs.get("body"),
                    )

                    records.requests[record.id] = record

                try:
                    response = original_method(*args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                return response

            urllib3.connectionpool.HTTPConnectionPool._make_request = _hook_make_request
    except ImportError:
        pass


def unset_hook_for_urllib3_make_request(records):
    try:
        import urllib3

        unset_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "_make_request",
            f"_httpdbg_original_make_request_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_urllib3_response_read(records):
    """Intercepts the HTTP requests"""
    try:
        import urllib3

        set_hook, original_method = can_set_hook(
            urllib3.response.HTTPResponse,
            "read",
            f"_httpdbg_original_read_{records.id}",
        )

        if set_hook:

            def _hook_read(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = None

                if record_request():
                    self = callargs.get("self")

                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                try:
                    content = original_method(*args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    if record.response.content:
                        record.response.content += content
                    else:
                        record.response.content = content

                return content

            urllib3.response.HTTPResponse.read = _hook_read
    except ImportError:
        pass


def unset_hook_for_urllib3_response_read(records):
    try:
        import urllib3

        unset_hook(
            urllib3.response.HTTPResponse,
            "read",
            f"_httpdbg_original_read_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_urllib3_response_read_chunked(records):
    """Intercepts the HTTP requests"""
    try:
        import urllib3

        set_hook, original_method = can_set_hook(
            urllib3.response.HTTPResponse,
            "read_chunked",
            f"_httpdbg_original_read_chunked_{records.id}",
        )

        if set_hook:

            def _hook_read_chunked(*args, **kwargs):
                callargs = getcallargs(original_method, *args, **kwargs)

                record = None

                if record_request():
                    self = callargs.get("self")
                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                try:
                    contents = original_method(*args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                # contents is a generator
                for content in contents:
                    if record:
                        if record.response.content:
                            record.response.content += content
                        else:
                            record.response.content = content

                    yield content

            urllib3.response.HTTPResponse.read_chunked = _hook_read_chunked
    except ImportError:
        pass


def unset_hook_for_urllib3_response_read_chunked(records):
    try:
        import urllib3

        unset_hook(
            urllib3.response.HTTPResponse,
            "read_chunked",
            f"_httpdbg_original_read_chunked_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_urllib3(records):
    set_hook_for_urllib3_make_request(records)
    set_hook_for_urllib3_urlopen(records)
    set_hook_for_urllib3_response_read(records)
    set_hook_for_urllib3_response_read_chunked(records)


def unset_hook_for_urllib3(records):
    unset_hook_for_urllib3_make_request(records)
    unset_hook_for_urllib3_urlopen(records)
    unset_hook_for_urllib3_response_read(records)
    unset_hook_for_urllib3_response_read_chunked(records)


def record_request():
    if os.environ.get("HTTPDBG_DEBUG", "0") == "1":
        return True

    already_recorded_by_the_requests_hook = False
    for line in traceback.format_stack():
        already_recorded_by_the_requests_hook |= in_lib(
            line,
            packages=[
                "requests",
            ],
        )

    return not already_recorded_by_the_requests_hook
