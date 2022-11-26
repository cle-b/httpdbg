# -*- coding: utf-8 -*-
import http
import secrets
import string
from urllib.parse import urlparse


def get_new_uuid():
    # important - the uuid must be compatible with method naming rules
    return "".join(secrets.choice(string.ascii_letters) for i in range(10))


class HTTPRecords:
    def __init__(self):
        self.id = get_new_uuid()
        self.requests = {}
        self.requests_already_loaded = 0

    @property
    def unread(self):
        return self.requests_already_loaded < len(self.requests)


class HTTPRecordContent:
    def __init__(self, headers, cookies, content):
        self.headers = self.list_headers(headers)
        self.cookies = self.list_cookies(headers, cookies)
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


class HTTPRecordContentUp(HTTPRecordContent):
    @staticmethod
    def list_cookies(headers, cookies):
        # important - do not use request._cookies as is because it contains all the cookies
        # of the session or redirection ; list only the cookies present in the raw header.
        lst = []
        for key, header in headers.items():
            if key.lower() == "cookie":
                for name, value in cookies.items():
                    if f"{name}={value}" in header:
                        madeleine = {"name": name, "value": value}
                        lst.append(madeleine)
        return lst


class HTTPRecordContentDown(HTTPRecordContent):
    @staticmethod
    def list_cookies(headers, cookies):
        # important - do not use response.cookies as is because it contains all the cookies
        # of the session or redirection ; list only the cookies present in the raw header.
        lst = []
        for key, header in headers.items():
            if key.lower() == "set-cookie":
                for cookie in cookies:
                    if f"{cookie.name}={cookie.value}" in header:
                        madeleine = {"name": cookie.name, "value": cookie.value}
                        attributes = []
                        # https://docs.python.org/3/library/http.cookiejar.html#cookie-objects
                        if cookie.port_specified:
                            attributes.append({"name": "port", "attr": cookie.port})
                        if cookie.domain_specified:
                            attributes.append({"name": "domain", "attr": cookie.domain})
                        if cookie.path:
                            attributes.append({"name": "path", "attr": cookie.path})
                        if cookie.comment:
                            attributes.append(
                                {"name": "comment", "attr": cookie.comment}
                            )
                        if cookie.comment_url:
                            attributes.append(
                                {"name": "comment_url", "attr": cookie.comment_url}
                            )
                        if cookie.expires:
                            attributes.append(
                                {
                                    "name": "expires",
                                    "attr": http.cookiejar.time2netscape(
                                        cookie.expires
                                    ),
                                }
                            )
                        if cookie.discard:
                            attributes.append({"name": "Discard"})
                        if cookie.secure:
                            attributes.append({"name": "Secure"})
                        if "httponly" in [k.lower() for k in cookie._rest.keys()]:
                            attributes.append({"name": "HttpOnly"})
                        if cookie._rest.get("SameSite"):
                            attributes.append(
                                {
                                    "name": "SameSite",
                                    "attr": cookie._rest.get("SameSite"),
                                }
                            )
                        if attributes:
                            madeleine["attributes"] = attributes
                        lst.append(madeleine)
        return lst


class HTTPRecord:
    def __init__(self):
        self.id = get_new_uuid()
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
