# -*- coding: utf-8 -*-
import asyncio
import asyncio.proactor_events
import datetime
import socket
import ssl
import sys
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Union

from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader
from httpdbg.initiator import Group
from httpdbg.initiator import Initiator
from httpdbg.preview import generate_preview
from httpdbg.utils import get_new_uuid
from httpdbg.utils import chunked_to_bytes
from httpdbg.utils import list_cookies_headers_request_simple_cookies
from httpdbg.utils import list_cookies_headers_response_simple_cookies
from httpdbg.log import logger


class SocketRawData(object):
    """Store the request data without encryption, even when using an SSLSocket."""

    def __init__(self, id: int, address: Tuple[str, int], ssl: bool) -> None:
        self.id: int = id
        self.address: Tuple[str, int] = address
        self.ssl: bool = ssl
        self._rawdata: bytes = bytes()
        self.record: Union[HTTPRecord, None] = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

    @property
    def rawdata(self) -> bytes:
        return self._rawdata

    @rawdata.setter
    def rawdata(self, value: bytes) -> None:
        logger().info(
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
        self._rawdata: bytes = bytes()
        self._rawheaders: bytes = bytes()
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

    @property
    def preview(self):
        return generate_preview(
            self.content,
            self.get_header("Content-Type"),
            self.get_header("Content-Encoding"),
        )

    @property
    def rawdata(self) -> bytes:
        return self._rawdata

    @rawdata.setter
    def rawdata(self, value: bytes):
        self.last_update = datetime.datetime.now(datetime.timezone.utc)
        self._rawdata = value


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
    def __init__(
        self,
        initiator_id: str = None,
        group_id: str = None,
        tag: str = None,
        tbegin: datetime.datetime = None,
        is_client: bool = True,
    ) -> None:
        self.id = get_new_uuid()
        self.address: Tuple[str, int] = ("", 0)
        self._url: Union[str, None] = None
        self.initiator_id: Union[str, None] = initiator_id
        self.exception: Union[Exception, None] = None
        self.request: HTTPRecordRequest = HTTPRecordRequest()
        self.response: HTTPRecordResponse = HTTPRecordResponse()
        self.ssl: Union[bool, None] = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.tag: Union[str, None] = tag
        self.group_id: Union[str, None] = group_id
        self.is_client: bool = is_client
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

    def receive_data(self, data: bytes):
        if self.is_client:
            self.response.rawdata += data
        else:
            self.request.rawdata += data

    def send_data(self, data: bytes):
        if self.is_client:
            self.request.rawdata += data
        else:
            self.response.rawdata += data

    @property
    def protocol(self) -> str:
        if self.response.protocol == self.request.protocol:
            return self.request.protocol
        else:
            return f"{self.request.protocol} -> {self.response.protocol}"


class HTTPRecordsSessionInfo:

    def __init__(self):
        self.id: str = get_new_uuid()
        self.command_line: str = " ".join(sys.argv[1:]) if sys.argv[1:] else "console"
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)


class HTTPRecords:
    def __init__(
        self,
        client: bool = True,
        server: bool = False,
        ignore: Union[List[Tuple[str, int]], None] = None,
    ) -> None:
        self.reset()
        self.client: bool = client
        self.server: bool = server
        self.ignore: List[Tuple[str, int]] = []
        if ignore:
            self.ignore = ignore

    def reset(self) -> None:
        logger().info("HTTPRecords.reset")
        self.session: HTTPRecordsSessionInfo = HTTPRecordsSessionInfo()
        self.requests: Dict[str, HTTPRecord] = {}
        self.requests_already_loaded = 0
        self.initiators: Dict[str, Initiator] = {}
        self.current_initiator: Union[str, None] = None
        self.groups: Dict[str, Group] = {}
        self.current_group: Union[str, None] = None
        self.current_tag: Union[str, None] = None
        self._sockets: Dict[int, SocketRawData] = {}

    @property
    def unread(self) -> int:
        return self.requests_already_loaded < len(self.requests)

    def __getitem__(self, item: int) -> HTTPRecord:
        return list(self.requests.values())[item]

    def __len__(self) -> int:
        return len(self.requests)

    def get_socket_data(
        self, obj, extra_sock=None, force_new=False, request=None, is_uvicorn=False
    ) -> Union[SocketRawData, None]:
        """Record a new SocketRawData (or get an existing one) and return it."""
        socketdata = None

        if force_new:
            self.del_socket_data(obj)

        if id(obj) in self._sockets:
            socketdata = self._sockets[id(obj)]
            if (
                request
                and socketdata
                and socketdata.record
                and socketdata.record.is_client
                and socketdata.record.response.rawdata
            ) or (
                (not request)
                and socketdata
                and socketdata.record
                and (not socketdata.record.is_client)
                and socketdata.record.request.rawdata
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
                    if address not in self.ignore:
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
            elif is_uvicorn:
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
                        if address not in self.ignore:
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
            logger().info(f"SocketRawData del id={id(obj)}")
            self._sockets[id(obj)] = None
            del self._sockets[id(obj)]

    def add_new_record_exception(
        self, initiator: Initiator, group: Group, url: str, exception: Exception
    ) -> HTTPRecord:
        if initiator.id not in self.initiators:
            self.initiators[initiator.id] = initiator
        new_record = HTTPRecord()
        new_record.url = url
        new_record.initiator_id = initiator.id
        new_record.group_id = group.id
        new_record.exception = exception
        self.requests[new_record.id] = new_record
        return new_record

    def add_initiator(self, initiator: Initiator):
        self.initiators[initiator.id] = initiator
        self.current_initiator = initiator.id

    def add_group(self, group: Group):
        self.groups[group.id] = group
        self.current_group = group.id

    def _print_for_debug(self):
        for request in self.requests.values():
            print(f"+ {request.url}")
            print(f"  - initiator: {self.initiators[request.initiator_id].label}")
            print(f"  - group: {self.groups[request.group_id].label}")
