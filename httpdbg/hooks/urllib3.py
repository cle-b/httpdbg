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


def set_hook_for_urllib3_urlopen(records):
    """Intercepts the HTTP requests"""
    try:
        import urllib3

        if can_set_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "urlopen",
            f"_httpdbg_original_urlopen_{records.id}",
        ):

            def _hook_urlopen(self, method, url, *args, **kwargs):

                record = None

                if record_request():

                    record = HTTPRecord()

                    record.initiator = get_initiator(records._initiators)

                    port = (
                        f":{self.port}"
                        if not (
                            ((self.scheme.upper() == "HTTP") and self.port == 80)
                            or ((self.scheme.upper() == "HTTPS") and self.port == 443)
                        )
                        else ""
                    )
                    record.url = f"{self.scheme}://{self.host}{port}{url}"
                    record.method = method
                    record.stream = False

                    self._httpdbg_record_id = record.id

                    records.requests[record.id] = record

                try:
                    response = getattr(
                        urllib3.connectionpool.HTTPConnectionPool,
                        f"_httpdbg_original_urlopen_{records.id}",
                    )(self, method, url, *args, **kwargs)
                except Exception as ex:
                    if record:
                        record.exception = ex
                        record.status_code = -1
                    raise

                if record:
                    record.response = HTTPRecordContentDown(
                        response.headers,
                        list_cookies_headers_response_simple_cookies(response.headers),
                        response._body,
                    )

                    record._reason = response.reason
                    record.status_code = response.status

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

        if can_set_hook(
            urllib3.connectionpool.HTTPConnectionPool,
            "_make_request",
            f"_httpdbg_original_make_request_{records.id}",
        ):

            def _hook_make_request(self, conn, method, url, *args, **kwargs):

                record = None

                if record_request():

                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                    record.request = HTTPRecordContentUp(
                        kwargs.get("headers"),
                        list_cookies_headers_request_simple_cookies(
                            kwargs.get("headers")
                        ),
                        kwargs.get("body"),
                    )

                    records.requests[record.id] = record

                try:
                    response = getattr(
                        urllib3.connectionpool.HTTPConnectionPool,
                        f"_httpdbg_original_make_request_{records.id}",
                    )(self, conn, method, url, *args, **kwargs)
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

        if can_set_hook(
            urllib3.response.HTTPResponse,
            "read",
            f"_httpdbg_original_read_{records.id}",
        ):

            def _hook_read(self, *args, **kwargs):

                record = None

                if record_request():

                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                try:
                    content = getattr(
                        urllib3.response.HTTPResponse,
                        f"_httpdbg_original_read_{records.id}",
                    )(self, *args, **kwargs)
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

        if can_set_hook(
            urllib3.response.HTTPResponse,
            "read_chunked",
            f"_httpdbg_original_read_chunked_{records.id}",
        ):

            def _hook_read_chunked(self, *args, **kwargs):

                record = None

                if record_request():
                    if hasattr(self, "_httpdbg_record_id"):
                        record = records.requests[self._httpdbg_record_id]

                try:
                    contents = getattr(
                        urllib3.response.HTTPResponse,
                        f"_httpdbg_original_read_chunked_{records.id}",
                    )(self, *args, **kwargs)
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
