# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import get_record
from httpdbg.hooks.utils import unset_hook
from httpdbg.hooks.utils import set_record

from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_httpconnection_init(records):
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection, "__init__", records
        )

        if set_hook:

            def _hook_init(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    is_https = isinstance(self, http.client.HTTPSConnection)
                    try:
                        import urllib3

                        is_https = is_https or isinstance(
                            self, urllib3.connectionpool.HTTPSConnection
                        )
                    except ImportError:
                        pass

                    scheme = "https" if is_https else "http"
                    host = callargs.get("host", "").split(":")[0]
                    port = callargs.get(
                        "port",
                        callargs.get("host").split(":")[1]
                        if callargs.get("host", "").find(":") > 0
                        else 80,
                    )
                    strport = (
                        f":{port}"
                        if not (
                            ((scheme.upper() == "HTTP") and port == 80)
                            or ((scheme.upper() == "HTTPS") and port == 443)
                        )
                        else ""
                    )
                    self._httpdbg_netloc = f"{scheme}://{host}{strport}"

                    try:
                        response = hooked_method(*args, **kwargs)
                    except Exception as ex:
                        record = HTTPRecord()
                        record.initiator = get_initiator(records._initiators)

                        record.url = self._httpdbg_netloc
                        record.exception = ex
                        record.status_code = -1

                        records.requests[record.id] = record

                        raise

                    return response

                return hook

            http.client.HTTPConnection.__init__ = _hook_init(
                http.client.HTTPConnection.__init__
            )
    except ImportError:
        pass


def unset_hook_for_httpconnection_init(records):
    try:
        import http

        unset_hook(http.client.HTTPConnection, "__init__", records)
    except ImportError:
        pass


def set_hook_for_httpconnection_request(records):
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection, "request", records
        )

        if set_hook:

            def _hook_request(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    record = None

                    if getattr(self, "_httpdbg_netloc", None):
                        record = HTTPRecord()
                        record.initiator = get_initiator(records._initiators)
                        records.requests[record.id] = record

                        record.url = f"{self._httpdbg_netloc}{callargs.get('url')}"
                        record.method = callargs.get("method")

                        headers = callargs.get("headers", {})
                        record.request = HTTPRecordContentUp(
                            headers,
                            list_cookies_headers_request_simple_cookies(headers),
                            callargs.get("body"),
                        )

                        set_record(records, record, self)

                    try:
                        response = hooked_method(*args, **kwargs)
                    except Exception as ex:
                        if record:
                            record.exception = ex
                            record.status_code = -1
                        raise

                    return response

                return hook

            http.client.HTTPConnection.request = _hook_request(
                http.client.HTTPConnection.request
            )
    except ImportError:
        pass


def unset_hook_for_httpconnection_request(records):
    try:
        import http

        unset_hook(http.client.HTTPConnection, "request", records)
    except ImportError:
        pass


def set_hook_for_httpconnection_getresponse(records):
    """Intercepts the HTTP requests"""
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection, "getresponse", records
        )

        if set_hook:

            def _hook_getresponse(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    record = get_record(records, self)

                    try:
                        response = hooked_method(*args, **kwargs)
                    except Exception as ex:
                        if record:
                            record.exception = ex
                            record.status_code = -1
                        raise

                    if record:
                        set_record(records, record, response)

                        record._reason = getattr(response, "reason", None)
                        record.status_code = getattr(response, "status", None)

                        headers = (
                            response.getheaders()
                            if getattr(response, "getheaders", False)
                            else None
                        )
                        record.response = HTTPRecordContentDown(
                            headers,
                            list_cookies_headers_response_simple_cookies(headers),
                            None,
                        )

                        def _hook_read(hooked_method):
                            def hook(self, *args, **kwargs):
                                data = hooked_method(self, *args, **kwargs)

                                if record.response.content is None:
                                    record.response.content = data
                                else:
                                    record.response.content += data
                                return data

                            return hook

                        response.fp.read = _hook_read(response.fp.read)

                    return response

                return hook

            http.client.HTTPConnection.getresponse = _hook_getresponse(
                http.client.HTTPConnection.getresponse
            )
    except ImportError:
        pass


def unset_hook_for_httpconnection_getresponse(records):
    try:
        import http

        unset_hook(http.client.HTTPConnection, "getresponse", records)
    except ImportError:
        pass


def set_hook_for_httpclient(records):
    set_hook_for_httpconnection_init(records)
    set_hook_for_httpconnection_request(records)
    set_hook_for_httpconnection_getresponse(records)


def unset_hook_for_httpclient(records):
    unset_hook_for_httpconnection_init(records)
    unset_hook_for_httpconnection_request(records)
    unset_hook_for_httpconnection_getresponse(records)
