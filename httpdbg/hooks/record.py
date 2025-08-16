# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
import datetime
from typing import Union

from httpdbg.utils import get_new_uuid
from httpdbg.utils import HTTPDBGCookie
from httpdbg.utils import HTTPDBGHeader


class HTTPRecordReqResp(ABC):

    @abstractmethod
    def get_header(self, name: str, default: str = "") -> str:
        pass

    @property
    @abstractmethod
    def rawheaders(self) -> bytes:
        pass

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

    @property
    @abstractmethod
    def rawdata(self) -> bytes:
        pass

    @rawdata.setter
    @abstractmethod
    def rawdata(self, value: bytes):
        pass


class HTTPRecordRequest(HTTPRecordReqResp, ABC):

    @property
    @abstractmethod
    def cookies(self) -> list[HTTPDBGCookie]:
        pass

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
    @abstractmethod
    def cookies(self) -> list[HTTPDBGCookie]:
        pass

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
        initiator_id: str = None,
        group_id: str = None,
        tag: str = None,
        tbegin: datetime.datetime = None,
        is_client: bool = True,
    ) -> None:
        self.id = get_new_uuid()
        self.address: tuple[str, int] = ("", 0)
        self._url: Union[str, None] = None
        self.initiator_id: Union[str, None] = initiator_id
        self.exception: Union[Exception, None] = None
        self.ssl: Union[bool, None] = None
        self.tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.tag: Union[str, None] = tag
        self.group_id: Union[str, None] = group_id
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
    @abstractmethod
    def method(self) -> str:
        pass

    @property
    @abstractmethod
    def status_code(self) -> int:
        pass

    @property
    @abstractmethod
    def reason(self) -> str:
        pass

    @property
    @abstractmethod
    def netloc(self) -> str:
        pass

    @property
    @abstractmethod
    def urlext(self) -> str:
        return self.url[len(self.netloc) :]

    @property
    @abstractmethod
    def in_progress(self) -> bool:
        pass

    @property
    @abstractmethod
    def last_update(self) -> datetime.datetime:
        pass

    @abstractmethod
    def receive_data(self, data: bytes):
        pass

    @abstractmethod
    def send_data(self, data: bytes):
        pass

    @property
    @abstractmethod
    def protocol(self) -> str:
        pass
