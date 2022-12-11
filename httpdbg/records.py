# -*- coding: utf-8 -*-
import time
from urllib.parse import urlparse

from httpdbg.utils import get_new_uuid


class HTTPRecords:
    def __init__(self):
        self.id = get_new_uuid()
        self.requests = {}
        self.requests_already_loaded = 0
        self._initiators = {}

    @property
    def unread(self):
        return self.requests_already_loaded < len(self.requests)

    def __getitem__(self, item):
        return list(self.requests.values())[item]

    def __len__(self):
        return len(self.requests)


class HTTPRecordContent:
    def __init__(self, headers, cookies, content):
        self.headers = self.list_headers(headers)
        self.cookies = cookies
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
    pass


class HTTPRecordContentDown(HTTPRecordContent):
    pass


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
        self.last_update = 0

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

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        self.__dict__["last_update"] = int(time.time() * 1000)
