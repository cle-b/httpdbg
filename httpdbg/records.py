# -*- coding: utf-8 -*-
import time
from urllib.parse import urlparse

from httpdbg.utils import get_new_uuid
from httpdbg.utils import chunked_to_bytes
from httpdbg.utils import list_cookies_headers_request_simple_cookies
from httpdbg.utils import list_cookies_headers_response_simple_cookies


class HTTPRecords:
    def __init__(self):
        self.id = get_new_uuid()
        self.requests = {}
        self.requests_already_loaded = 0
        self._initiators = {}
        self.sockets = {}

    @property
    def unread(self):
        return self.requests_already_loaded < len(self.requests)

    def __getitem__(self, item):
        return list(self.requests.values())[item]

    def __len__(self):
        return len(self.requests)


class HTTPRecordReq(object):
    def __init__(self):
        self.rawdata = bytes()
        self._rawheaders = bytes()
        self._headers = []
        self.last_update = 0

    def get_header(self, name):
        for header in self.headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    @property
    def rawheaders(self):
        if not self._rawheaders:
            sep = self.rawdata.find(b"\r\n\r\n")
            if sep > -1:
                self._rawheaders = self.rawdata[:sep]
        return self._rawheaders

    @property
    def headers(self):
        if not self._headers:
            if self.rawheaders:
                for header in self.rawheaders[self.rawheaders.find(b"\r\n") :].split(
                    b"\r\n"
                ):
                    sh = header.split(b":")
                    name = sh[0]
                    value = b":".join(sh[1:])
                    if name:
                        self._headers.append(
                            {
                                "name": name.decode().strip(),
                                "value": value.decode().strip(),
                            }
                        )
        return self._headers

    @property
    def content(self):
        rawdata = bytes()

        sep = self.rawdata.find(b"\r\n\r\n")
        if sep > -1:
            rawcontent = self.rawdata[sep + 4 :]

            content_length = self.get_header("Content-Length")

            if content_length:
                rawdata = rawcontent[: min(len(rawcontent), int(content_length))]
            elif "chunked" in self.get_header("Transfer-Encoding").lower():
                rawdata = chunked_to_bytes(rawcontent)
            else:
                rawdata = rawcontent

        return rawdata

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        self.__dict__["last_update"] = int(time.time() * 1000)


class HTTPRecordRequest(HTTPRecordReq):
    def __init__(self):
        super().__init__()
        self._method = bytes()
        self._uri = bytes()
        self._protocol = bytes()

    @property
    def cookies(self):
        return list_cookies_headers_request_simple_cookies(self.headers)

    def _parse_first_line(self):
        if self.rawheaders:
            firstline = self.rawheaders[: self.rawheaders.find(b"\r\n")]
            self._method, self._uri, self._protocol = firstline.split(b" ")

    @property
    def method(self):
        if not self._method:
            self._parse_first_line()
        return self._method.decode()

    @property
    def uri(self):
        if not self._uri:
            self._parse_first_line()
        return self._uri.decode()

    @property
    def protocol(self):
        if not self._protocol:
            self._parse_first_line()
        return self._protocol.decode()


class HTTPRecordResponse(HTTPRecordReq):
    def __init__(self):
        super().__init__()
        self._protocol = bytes()
        self._status_code = bytes()
        self._message = bytes()

    @property
    def cookies(self):
        return list_cookies_headers_response_simple_cookies(self.headers)

    def _parse_first_line(self):
        if self.rawheaders:
            firstline = self.rawheaders[: self.rawheaders.find(b"\r\n")]
            self._protocol, self._status_code, self._message = firstline.split(b" ", 2)

    @property
    def protocol(self):
        if not self._protocol:
            self._parse_first_line()
        return self._protocol.decode()

    @property
    def status_code(self):
        if not self._status_code:
            self._parse_first_line()
        return int(self._status_code.decode()) if self._status_code else -1

    @property
    def message(self):
        if not self._message:
            self._parse_first_line()
        return self._message.decode()


class HTTPRecord:
    def __init__(self):
        self.id = get_new_uuid()
        self.address = None
        self._url = None
        self.initiator = None
        self.exception = None
        self.request = HTTPRecordRequest()
        self.response = HTTPRecordResponse()
        self.ssl = None

    @property
    def url(self):
        if not self._url:
            address = self.request.get_header("host").split(":") or self.address
            host = address[0]
            port = address[1] if len(address) == 2 else None
            sport = ""
            if self.ssl:
                scheme = "https"
                if port:
                    sport = f":{port}" if port != "443" else ""
            else:
                scheme = "http"
                if port:
                    sport = f":{port}" if port != "80" else ""
            self._url = f"{scheme}://{host}{sport}{self.request.uri}"
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def method(self):
        return self.request.method

    @property
    def status_code(self):
        return self.response.status_code if self.response.status_code else -1

    @property
    def reason(self):
        desc = "in progress"
        if self.response.message:
            desc = self.response.message
        elif self.exception is not None:
            desc = getattr(type(self.exception), "__name__", str(type(self.exception)))
        return desc

    @property
    def netloc(self):
        url = urlparse(self.url)
        return f"{url.scheme}://{url.netloc}"

    @property
    def urlext(self):
        return self.url[len(self.netloc) :]

    @property
    def last_update(self):
        return max(self.request.last_update, self.response.last_update)
