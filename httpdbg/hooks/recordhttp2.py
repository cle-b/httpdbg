import datetime

from httpdbg.preview import generate_preview
from httpdbg.hooks.record import HTTPRecord
from httpdbg.hooks.record import HTTPRecordReqResp
from httpdbg.hooks.record import HTTPRecordRequest
from httpdbg.hooks.record import HTTPRecordResponse
from httpdbg.http_status_code import HTTP_STATUS_CODE_MESSAGE
from httpdbg.utils import HTTPDBGHeader


class HTTP2RecordReqResp(HTTPRecordReqResp):
    def __init__(self) -> None:
        super().__init__()
        self._content: bytes = bytes()
        self._headers: list[HTTPDBGHeader] = list()

    @property
    def content(self) -> bytes:
        return self._content

    @content.setter
    def content(self, value: bytes):
        self.last_update = datetime.datetime.now(datetime.timezone.utc)
        self._content = value

    @property
    def headers(self) -> list[HTTPDBGHeader]:
        return self._headers

    @headers.setter
    def headers(self, values: list[tuple[bytes, bytes]]) -> None:
        for header in values:
            self._headers.append(HTTPDBGHeader(header[0].decode(), header[1].decode()))

    @property
    def preview(self):
        return generate_preview(
            self.content,
            self.get_header("Content-Type"),
            self.get_header("Content-Encoding"),
        )


class HTTP2RecordRequest(HTTPRecordRequest, HTTP2RecordReqResp):

    @property
    def method(self) -> str:
        return self.get_header(":method")

    @property
    def uri(self) -> str:
        return self.get_header(":path")

    @property
    def protocol(self) -> str:
        return "HTTP/2"


class HTTP2RecordResponse(HTTPRecordResponse, HTTP2RecordReqResp):

    @property
    def protocol(self) -> str:
        return "HTTP/2"

    @property
    def status_code(self) -> int:
        return int(self.get_header(":status", "0"))

    @property
    def message(self) -> str:
        return HTTP_STATUS_CODE_MESSAGE.get(self.status_code, "")


class HTTP2Record(HTTPRecord):
    def __init__(
        self,
        initiator_id: str,
        group_id: str,
        tag: str = None,
        tbegin: datetime.datetime = None,
        is_client: bool = True,
    ) -> None:
        super().__init__(initiator_id, group_id, tag, tbegin, is_client)
        self.request: HTTP2RecordRequest = HTTP2RecordRequest()
        self.response: HTTP2RecordResponse = HTTP2RecordResponse()

    @property
    def url(self) -> str:
        if not self._url:
            self._url = (
                self.request.get_header(":scheme")
                + "://"
                + self.request.get_header(":authority")
                + self.request.uri
            )
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    def receive_data(self, data: bytes):
        if self.is_client:
            self.response.content += data
        else:
            self.request.content += data

    def send_data(self, data: bytes):
        if self.is_client:
            self.request.content += data
        else:
            self.response.content += data
