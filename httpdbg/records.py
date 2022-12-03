# -*- coding: utf-8 -*-
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
