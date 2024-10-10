# -*- coding: utf-8 -*-
import asyncio
import asyncio.proactor_events
import datetime
import os
import socket
import ssl
import traceback
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Union

from httpdbg.env import HTTPDBG_CURRENT_INITIATOR
from httpdbg.env import HTTPDBG_CURRENT_TAG
from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader
from httpdbg.initiator import in_lib
from httpdbg.initiator import Initiator
from httpdbg.preview import generate_preview
from httpdbg.utils import get_new_uuid
from httpdbg.utils import chunked_to_bytes
from httpdbg.utils import list_cookies_headers_request_simple_cookies
from httpdbg.utils import list_cookies_headers_response_simple_cookies
from httpdbg.utils import logger


class SocketRawData(object):
    def __init__(self, id: int, address: Tuple[str, int], ssl: bool) -> None:
        self.id = id
        self.address = address
        self.ssl = ssl
        self._rawdata = bytes()
        self.record = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

    @property
    def rawdata(self) -> bytes:
        return self._rawdata

    @rawdata.setter
    def rawdata(self, value: bytes) -> None:
        logger.info(
            f"SocketRawData id={self.id} newdata={value[:20]!r} len={len(value)}"
        )
        self._rawdata = value

    def http_detected(self) -> Union[bool, None]:
        end_of_first_line = self.rawdata[:2048].find(b"\r\n")
        if end_of_first_line == -1:
            if len(self.rawdata) > 2048:
                return False
            else:
                return None
        firstline = self.rawdata[:end_of_first_line]
        if firstline.upper().endswith(b"HTTP/1.1"):
            return True
        if firstline.upper().endswith(b"HTTP/1.0"):
            return True
        return False

    def __repr__(self) -> str:
        return f"SocketRawData id={self.id} {self.address}"


class HTTPRecordReqResp(object):
    def __init__(self) -> None:
        self.rawdata = bytes()
        self._rawheaders = bytes()
        self._headers: List[HTTPDBGHeader] = []
        self.last_update: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        )

    def get_header(self, name: str, default: str = "") -> str:
        for header in self.headers:
            if header.name.lower() == name.lower():
                return header.value
        return default

    @property
    def rawheaders(self) -> bytes:
        if not self._rawheaders:
            sep = self.rawdata.find(b"\r\n\r\n")
            if sep > -1:
                self._rawheaders = self.rawdata[:sep]
        return self._rawheaders

    @property
    def headers(self) -> List[HTTPDBGHeader]:
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
                            HTTPDBGHeader(name.decode().strip(), value.decode().strip())
                        )
        return self._headers

    @property
    def content(self) -> bytes:
        rawdata = bytes()

        sep = self.rawdata.find(b"\r\n\r\n")
        if sep > -1:
            rawcontent = self.rawdata[sep + 4 :]

            content_length = self.get_header("Content-Length")

            if content_length:
                rawdata = rawcontent[: min(len(rawcontent), int(content_length))]
            elif "chunked" in self.get_header("Transfer-Encoding", "").lower():
                rawdata = chunked_to_bytes(rawcontent)
            else:
                rawdata = rawcontent

        return rawdata

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        self.__dict__["last_update"] = datetime.datetime.now(datetime.timezone.utc)

    @property
    def preview(self):
        return generate_preview(
            self.content,
            self.get_header("Content-Type"),
            self.get_header("Content-Encoding"),
        )


class HTTPRecordRequest(HTTPRecordReqResp):
    def __init__(self) -> None:
        super().__init__()
        self._method = bytes()
        self._uri = bytes()
        self._protocol = bytes()

    @property
    def cookies(self) -> List[HTTPDBGCookie]:
        return list_cookies_headers_request_simple_cookies(self.headers)

    def _parse_first_line(self) -> None:
        if self.rawheaders:
            firstline = self.rawheaders[: self.rawheaders.find(b"\r\n")]
            self._method, self._uri, self._protocol = firstline.split(b" ")

    @property
    def method(self) -> str:
        if not self._method:
            self._parse_first_line()
        return self._method.decode()

    @property
    def uri(self) -> str:
        if not self._uri:
            self._parse_first_line()
        return self._uri.decode()

    @property
    def protocol(self) -> str:
        if not self._protocol:
            self._parse_first_line()
        return self._protocol.decode()


class HTTPRecordResponse(HTTPRecordReqResp):
    def __init__(self):
        super().__init__()
        self._protocol = bytes()
        self._status_code = bytes()
        self._message = bytes()

    @property
    def cookies(self) -> List[HTTPDBGCookie]:
        return list_cookies_headers_response_simple_cookies(self.headers)

    def _parse_first_line(self) -> None:
        if self.rawheaders:
            firstline = self.rawheaders[: self.rawheaders.find(b"\r\n")]
            self._protocol, self._status_code, self._message = firstline.split(b" ", 2)

    @property
    def protocol(self) -> str:
        if not self._protocol:
            self._parse_first_line()
        return self._protocol.decode()

    @property
    def status_code(self) -> int:
        if not self._status_code:
            self._parse_first_line()
        return int(self._status_code.decode()) if self._status_code else 0

    @property
    def message(self) -> str:
        if not self._message:
            self._parse_first_line()
        return self._message.decode()


class HTTPRecord:
    def __init__(self, tbegin: datetime.datetime = None) -> None:
        self.id = get_new_uuid()
        self.address: Tuple[str, int] = ("", 0)
        self._url: Union[str, None] = None
        self.initiator: Initiator = Initiator("", "", None, "", [])
        self.exception: Union[Exception, None] = None
        self.request: HTTPRecordRequest = HTTPRecordRequest()
        self.response: HTTPRecordResponse = HTTPRecordResponse()
        self.ssl: Union[bool, None] = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.tag = os.environ.get(HTTPDBG_CURRENT_TAG)
        if tbegin:
            self.tbegin = tbegin

    @property
    def url(self) -> str:
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
    def url(self, value: str) -> None:
        self._url = value

    @property
    def method(self) -> str:
        return self.request.method

    @property
    def status_code(self) -> int:
        if self.exception:
            return -1
        else:
            return self.response.status_code if self.response.status_code else 0

    @property
    def reason(self) -> str:
        desc = "in progress"
        if self.response.message:
            desc = self.response.message
        elif self.exception is not None:
            desc = getattr(type(self.exception), "__name__", str(type(self.exception)))
        return desc

    @property
    def netloc(self) -> str:
        url = urlparse(self.url)
        return f"{url.scheme}://{url.netloc}"

    @property
    def urlext(self) -> str:
        return self.url[len(self.netloc) :]

    @property
    def in_progress(self) -> bool:
        try:
            length = int(self.response.get_header("Content-Length", "0"))
            if length:
                return len(self.response.content) < length
        except Exception:
            pass
        return False

    @property
    def last_update(self) -> datetime.datetime:
        return max(self.request.last_update, self.response.last_update)


class HTTPRecords:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.id = get_new_uuid()
        self.requests: Dict[str, HTTPRecord] = {}
        self.requests_already_loaded = 0
        self._initiators: Dict[str, Initiator] = {}
        self._sockets: Dict[int, SocketRawData] = {}

    @property
    def unread(self) -> int:
        return self.requests_already_loaded < len(self.requests)

    def __getitem__(self, item: int) -> HTTPRecord:
        return list(self.requests.values())[item]

    def __len__(self) -> int:
        return len(self.requests)

    def get_initiator(self) -> Initiator:
        envname = f"{HTTPDBG_CURRENT_INITIATOR}_{self.id}"

        if envname in os.environ:
            initiator = self._initiators[os.environ[envname]]
        else:
            fullstack = traceback.format_stack()
            stack: List[str] = []
            for line in fullstack[6:]:
                if in_lib(line):
                    break
                stack.append(line)
            long_label = stack[-1]
            short_label = long_label.split("\n")[1]
            initiator = Initiator(get_new_uuid(), short_label, None, long_label, stack)

        if ("PYTEST_CURRENT_TEST" in os.environ) and (
            "HTTPDBG_PYTEST_PLUGIN" not in os.environ
        ):
            long_label = " ".join(os.environ["PYTEST_CURRENT_TEST"].split(" ")[:-1])
            short_label = long_label.split("::")[-1]
            initiator = Initiator(
                f"{long_label}{self.id}",
                short_label,
                long_label,
                initiator.short_stack,
                initiator.stack,
            )

        return initiator

    def get_socket_data(
        self, obj, extra_sock=None, force_new=False, request=None
    ) -> Union[SocketRawData, None]:
        socketdata = None

        if force_new:
            self.del_socket_data(obj)

        if id(obj) in self._sockets:
            socketdata = self._sockets[id(obj)]
            if request:
                if (
                    socketdata
                    and socketdata.record
                    and socketdata.record.response.rawdata
                ):
                    # the socket is reused for a new request
                    self._sockets[id(obj)] = SocketRawData(
                        id(obj), socketdata.address, socketdata.ssl
                    )
                    socketdata = self._sockets[id(obj)]
        else:
            if isinstance(obj, socket.socket):
                try:
                    address = obj.getsockname()
                    self._sockets[id(obj)] = SocketRawData(
                        id(obj), address, isinstance(obj, ssl.SSLSocket)
                    )
                    socketdata = self._sockets[id(obj)]
                except OSError:
                    # OSError: [WinError 10022] An invalid argument was supplied
                    pass
            elif isinstance(obj, asyncio.proactor_events._ProactorSocketTransport):
                # only for async HTTP requests (not HTTPS) on Windows
                self._sockets[id(obj)] = SocketRawData(id(obj), ("", 0), False)
                socketdata = self._sockets[id(obj)]
            else:
                if extra_sock:
                    try:
                        address = (
                            extra_sock.getsockname()
                            if hasattr(extra_sock, "getsockname")
                            else ("", 0)  # wrap_bio
                        )
                        self._sockets[id(obj)] = SocketRawData(
                            id(obj),
                            address,
                            isinstance(obj, (ssl.SSLObject, ssl.SSLSocket)),
                        )
                        socketdata = self._sockets[id(obj)]
                    except OSError:
                        # OSError: [WinError 10022] An invalid argument was supplied
                        pass

        return socketdata

    def move_socket_data(self, dest, ori):
        if id(ori) in self._sockets:
            socketdata = self.get_socket_data(ori)
            if socketdata:
                self._sockets[id(dest)] = socketdata
                if isinstance(dest, (ssl.SSLSocket, ssl.SSLObject)):
                    socketdata.ssl = True
                self.del_socket_data(ori)

    def del_socket_data(self, obj):
        if id(obj) in self._sockets:
            logger.info(f"SocketRawData del id={id(obj)}")
            self._sockets[id(obj)] = None
            del self._sockets[id(obj)]
