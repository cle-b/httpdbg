# -*- coding: utf-8 -*-
from httpdbg.initiator import get_initiator
from httpdbg.hooks.cookies import list_cookies_headers_request_simple_cookies
from httpdbg.hooks.cookies import list_cookies_headers_response_simple_cookies
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import can_set_hook
from httpdbg.hooks.utils import unset_hook
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecordContentDown
from httpdbg.records import HTTPRecordContentUp


def set_hook_for_httpconnection_init(records):
    """Intercepts the HTTP requests"""
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection, "__init__", f"_original_init_{records.id}"
        )

        if set_hook:

            def _hook_init(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    host = callargs.get("host", "").split(":")[0]
                    port = callargs.get(
                        "port",
                        callargs.get("host").split(":")[1]
                        if callargs.get("host", "").find(":") > 0
                        else 80,
                    )
                    self._httpdbg_netloc = (
                        f"http://{host}{f':{port}' if port != 80 else ''}"
                    )

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

        unset_hook(
            http.client.HTTPConnection,
            "__init__",
            f"_original_init_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpconnection_request(records):
    """Intercepts the HTTP requests"""
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection, "request", f"_original_request_{records.id}"
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

                        print("#" * 40)
                        print(callargs.get("url"))

                        record.url = f"{self._httpdbg_netloc}{callargs.get('url')}"
                        record.method = callargs.get("method")

                        headers = callargs.get("headers", {})
                        record.request = HTTPRecordContentUp(
                            headers,
                            list_cookies_headers_request_simple_cookies(headers),
                            callargs.get("body"),
                        )

                        setattr(self, f"_httpdbg_{records.id}_record_id", record.id)

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

        unset_hook(
            http.client.HTTPConnection,
            "request",
            f"_original_request_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpconnection_getresponse(records):
    """Intercepts the HTTP requests"""
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPConnection,
            "getresponse",
            f"_original_getresponse_{records.id}",
        )

        if set_hook:

            def _hook_getresponse(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    record = None

                    record_id = getattr(self, f"_httpdbg_{records.id}_record_id", None)
                    if record_id:
                        record = records.requests[record_id]

                    try:
                        response = hooked_method(*args, **kwargs)
                    except Exception as ex:
                        if record:
                            record.exception = ex
                            record.status_code = -1
                        raise

                    if record:
                        setattr(response, f"_httpdbg_{records.id}_record_id", record.id)
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

        unset_hook(
            http.client.HTTPConnection,
            "getresponse",
            f"_original_getresponse_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpresponse_read(records):
    """Intercepts the HTTP requests"""
    try:
        import http

        set_hook, original_method = can_set_hook(
            http.client.HTTPResponse, "read", f"_original_read_{records.id}"
        )

        if set_hook:

            def _hook_read(hooked_method):
                def hook(*args, **kwargs):
                    callargs = getcallargs(original_method, *args, **kwargs)

                    self = callargs["self"]

                    record = None

                    record_id = getattr(self, f"_httpdbg_{records.id}_record_id", None)

                    if record_id:
                        record = records.requests[record_id]

                    try:
                        data = hooked_method(*args, **kwargs)
                    except Exception as ex:
                        if record:
                            record.exception = ex
                            record.status_code = -1
                        raise

                    if record:
                        if record.response.content is None:
                            record.response.content = data
                        else:
                            record.response.content += data

                    return data

                return hook

            http.client.HTTPResponse.read = _hook_read(http.client.HTTPResponse.read)
    except ImportError:
        pass


def unset_hook_for_httpresponse_read(records):
    try:
        import http

        unset_hook(
            http.client.HTTPResponse,
            "read",
            f"_original_read_{records.id}",
        )
    except ImportError:
        pass


def set_hook_for_httpclient(records):
    set_hook_for_httpconnection_init(records)
    set_hook_for_httpconnection_request(records)
    set_hook_for_httpconnection_getresponse(records)
    set_hook_for_httpresponse_read(records)
    # TODO HTTPConnection.send(data)
    # TODO HTTPConnection.endheaders
    # TODO HTTPConnection.putheader
    # TODO HTTPConnection.putrequest
    # TODO HTTPResponse.readinto(b)


def unset_hook_for_httpclient(records):
    unset_hook_for_httpconnection_init(records)
    unset_hook_for_httpconnection_request(records)
    unset_hook_for_httpconnection_getresponse(records)
    unset_hook_for_httpresponse_read(records)
