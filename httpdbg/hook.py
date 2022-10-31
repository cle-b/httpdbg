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


class HTTPRecord:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.unread = True
        self._request = None
        self._response = None
        self.initiator = None
        self.exception = None

    @property
    def request(self):
        self.unread = False
        return self._request

    @request.setter
    def request(self, r):
        self.unread = True
        self._request = r

    @property
    def response(self):
        self.unread = False
        return self._response

    @response.setter
    def response(self, r):
        self.unread = True
        self._response = r

    @property
    def status_code(self):
        code = 0
        if self.exception is not None:
            code = -1
        elif self.response is not None:
            code = self.response.status_code
        return code

    @property
    def reason(self):
        desc = "in progress"
        if self.exception is not None:
            desc = getattr(type(self.exception), "__name__", str(type(self.exception)))
        elif self.response is not None:
            desc = self.response.reason
        return desc

    @staticmethod
    def list_headers(headers):
        lst = []
        for name, value in headers.items():
            lst.append({"name": name, "value": value})
        return lst

    @staticmethod
    def get_header(headers, name):
        for _name, value in headers.items():
            if _name.lower() == name.lower():
                return value
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

    @property
    def url(self):
        return self.request.url

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

    if not hasattr(requests.Session, "_original_send"):

        mixtape.reset()

        requests.Session._original_send = requests.Session.send

        def _hook_send(session, request, **kwargs):

            record = HTTPRecord()
            record.initiator = get_initiator()
            record.request = request

            mixtape.requests[record.id] = record
            record.stream = kwargs.get("stream", False)

            try:
                response = requests.Session._original_send(session, request, **kwargs)
            except Exception as ex:
                record.exception = ex
                raise

            record.response = response

            return response

        requests.Session.send = _hook_send


def unset_hook():
    import requests

    if hasattr(requests.Session, "_original_send"):
        requests.Session.send = requests.Session._original_send
        delattr(requests.Session, "_original_send")
