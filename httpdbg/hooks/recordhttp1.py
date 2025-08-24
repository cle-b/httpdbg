import datetime

from httpdbg.preview import generate_preview
from httpdbg.hooks.record import HTTPRecord
from httpdbg.hooks.record import HTTPRecordReqResp
from httpdbg.hooks.record import HTTPRecordRequest
from httpdbg.hooks.record import HTTPRecordResponse
from httpdbg.utils import chunked_to_bytes
from httpdbg.utils import HTTPDBGHeader


class HTTP1RecordReqResp(HTTPRecordReqResp):
    def __init__(self) -> None:
        super().__init__()
        self._rawdata: bytes = bytes()
        self._rawheaders: bytes = bytes()
        self._headers: list[HTTPDBGHeader] = []

    @property
    def rawheaders(self) -> bytes:
        if not self._rawheaders:
            sep = self.rawdata.find(b"\r\n\r\n")
            if sep > -1:
                self._rawheaders = self.rawdata[:sep]
        return self._rawheaders

    @property
    def headers(self) -> list[HTTPDBGHeader]:
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


class HTTP1RecordRequest(HTTPRecordRequest, HTTP1RecordReqResp):
    def __init__(self) -> None:
        super().__init__()
        self._method = bytes()
        self._uri = bytes()
        self._protocol = bytes()

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


class HTTP1RecordResponse(HTTPRecordResponse, HTTP1RecordReqResp):
    def __init__(self):
        super().__init__()
        self._protocol = bytes()
        self._status_code = bytes()
        self._message = bytes()

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


class HTTP1Record(HTTPRecord):
    def __init__(
        self,
        initiator_id: str,
        group_id: str,
        tag: str = None,
        tbegin: datetime.datetime = None,
        is_client: bool = True,
    ) -> None:
        super().__init__(initiator_id, group_id, tag, tbegin, is_client)
        self.request: HTTP1RecordRequest = HTTP1RecordRequest()
        self.response: HTTP1RecordResponse = HTTP1RecordResponse()

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

    def receive_data(self, data: bytes):
        if self.is_client:
            self.response.rawdata += data
            if self.response.rawdata.lower() in {
                b"http/1.1 100 continue\r\n\r\n",
                b"http/1.0 100 continue\r\n\r\n",
            }:
                # in case we receive an HTTP 100 code, we do not record it as the final HTTP response headers
                # but we keep the information to display it in the UI
                self.http100 = True
                self.response.rawdata = (
                    bytes()
                )  # very important to have the HTTP request body recorded.
        else:
            self.request.rawdata += data

    def send_data(self, data: bytes):
        if self.is_client:
            self.request.rawdata += data
        else:
            self.response.rawdata += data
