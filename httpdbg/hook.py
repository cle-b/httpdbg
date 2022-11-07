# -*- coding: utf-8 -*-
from http.cookies import SimpleCookie
import uuid
from urllib.parse import urlparse

from httpdbg.initiator import get_initiator


class HTTPRecords:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.requests = {}
        self.requests_already_loaded = 0

    def reset(self):
        self.id = str(uuid.uuid4())
        self.requests = {}
        self.requests_already_loaded = 0

    @property
    def unread(self):
        return self.requests_already_loaded < len(self.requests)


class HTTPRecordContent:
    def __init__(self, headers, content):
        self.headers = self.list_headers(headers)
        self.cookies = self.list_cookies(headers)
        self.content = content

    @staticmethod
    def list_headers(headers):
        lst = []
        for name, value in headers.items():
            lst.append({"name": name, "value": value})
        return lst

    def get_header(self, name):
        for header in self.headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    @staticmethod
    def list_cookies(headers):
        # important - do not use request._cookies or response.cookies as they contain
        # all the cookies of the session or redirection
        lst = []
        for key, header in headers.items():
            if key.lower() in ["set-cookie", "cookie"]:
                sc = SimpleCookie()
                sc.load(header)
                for name, cookie in sc.items():
                    madeleine = {"name": name, "value": cookie.value}
                    attributes = []
                    for attr_name, attr_value in cookie.items():
                        if attr_name == "secure":
                            attr_name = "Secure"
                        if attr_name == "httponly":
                            attr_name = "HttpOnly"
                        if attr_name == "samesite":
                            attr_name = "SameSite"
                        if isinstance(attr_value, bool):
                            if attr_value:
                                attributes.append({"name": attr_name})
                        elif attr_value != "":
                            attributes.append({"name": attr_name, "attr": attr_value})
                    if attributes:
                        madeleine["attributes"] = attributes
                    lst.append(madeleine)
        return lst


class HTTPRecord:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.initiator = None
        self.exception = None
        self.url = None
        self.method = None
        self.stream = None
        self.status_code = 0
        self._reason = None
        self.request = None
        self.response = None

    @property
    def reason(self):
        desc = "in progress"
        if self.exception is not None:
            desc = getattr(type(self.exception), "__name__", str(type(self.exception)))
        elif self.response is not None:
            desc = self._reason
        return desc

    @property
    def netloc(self):
        url = urlparse(self.url)
        return f"{url.scheme}://{url.netloc}"

    @property
    def urlext(self):
        return self.url[len(self.netloc) :]


def set_hook(mixtape):
    """Intercepts the HTTP requests"""
    import requests

    if not hasattr(requests.adapters.HTTPAdapter, "_original_send"):

        mixtape.reset()

        requests.adapters.HTTPAdapter._original_send = (
            requests.adapters.HTTPAdapter.send
        )

        def _hook_send(self, request, **kwargs):

            record = HTTPRecord()

            record.initiator = get_initiator()

            record.url = request.url
            record.method = request.method
            record.stream = kwargs.get("stream", False)
            record.request = HTTPRecordContent(request.headers, request.body)

            mixtape.requests[record.id] = record

            try:
                response = requests.adapters.HTTPAdapter._original_send(
                    self, request, **kwargs
                )
            except Exception as ex:
                record.exception = ex
                record.status_code = -1
                raise

            record.response = HTTPRecordContent(
                response.headers, response.content if not record.stream else None
            )
            record._reason = response.reason
            # change the status_code at the end to be sure the ui reload a fresh description of the request
            record.status_code = response.status_code

            return response

        requests.adapters.HTTPAdapter.send = _hook_send


def unset_hook():
    import requests

    if hasattr(requests.adapters.HTTPAdapter, "_original_send"):
        requests.adapters.HTTPAdapter.send = (
            requests.adapters.HTTPAdapter._original_send
        )
        delattr(requests.adapters.HTTPAdapter, "_original_send")
