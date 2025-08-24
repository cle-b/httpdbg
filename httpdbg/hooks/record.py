from abc import ABC, abstractmethod
import datetime
from typing import Union
from urllib.parse import urlparse

from httpdbg.utils import get_new_uuid
from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader
from httpdbg.utils import list_cookies_headers_request_simple_cookies
from httpdbg.utils import list_cookies_headers_response_simple_cookies


class HTTPRecordReqResp(ABC):

    def __init__(self) -> None:
        self.last_update: datetime.datetime = datetime.datetime.now(
            datetime.timezone.utc
        )

    def get_header(self, name: str, default: str = "") -> str:
        for header in self.headers:
            if header.name.lower() == name.lower():
                return header.value
        return default

    @property
    @abstractmethod
    def headers(self) -> list[HTTPDBGHeader]:
        pass

    @property
    @abstractmethod
    def content(self) -> bytes:
        pass

    @property
    @abstractmethod
    def preview(self):
        pass


class HTTPRecordRequest(HTTPRecordReqResp, ABC):

    @property
    def cookies(self) -> list[HTTPDBGCookie]:
        return list_cookies_headers_request_simple_cookies(self.headers)

    @property
    @abstractmethod
    def method(self) -> str:
        pass

    @property
    @abstractmethod
    def uri(self) -> str:
        pass

    @property
    @abstractmethod
    def protocol(self) -> str:
        pass


class HTTPRecordResponse(HTTPRecordReqResp, ABC):

    @property
    def cookies(self) -> list[HTTPDBGCookie]:
        return list_cookies_headers_response_simple_cookies(self.headers)

    @property
    @abstractmethod
    def protocol(self) -> str:
        pass

    @property
    @abstractmethod
    def status_code(self) -> int:
        pass

    @property
    @abstractmethod
    def message(self) -> str:
        pass


class HTTPRecord(ABC):
    request: HTTPRecordRequest
    response: HTTPRecordResponse

    @abstractmethod
    def __init__(
        self,
        initiator_id: str,
        group_id: str,
        tag: str = None,
        tbegin: datetime.datetime = None,
        is_client: bool = True,
    ) -> None:
        self.id = get_new_uuid()
        self.address: tuple[str, int] = ("", 0)
        self._url: Union[str, None] = None
        self.initiator_id: str = initiator_id
        self.exception: Union[Exception, None] = None
        self.ssl: Union[bool, None] = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.tag: Union[str, None] = tag
        self.group_id: str = group_id
        self.is_client: bool = is_client
        if tbegin:
            self.tbegin = tbegin
        self.http100: bool = False

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @url.setter
    @abstractmethod
    def url(self, value: str) -> None:
        pass

    @property
    def urlext(self) -> str:
        return self.url[len(self.netloc) :]

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

    @abstractmethod
    def receive_data(self, data: bytes):
        pass

    @abstractmethod
    def send_data(self, data: bytes):
        pass

    @property
    def protocol(self) -> str:
        if self.response.protocol == self.request.protocol:
            return self.request.protocol
        else:
            return f"{self.request.protocol} -> {self.response.protocol}"
