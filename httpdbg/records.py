import datetime
import sys
from typing import Union

from httpdbg.hooks.record import HTTPRecord
from httpdbg.initiator import Group
from httpdbg.initiator import Initiator
from httpdbg.log import logger
from httpdbg.utils import get_new_uuid


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
        ignore: tuple[tuple[str, int], ...] = (),
    ) -> None:
        self.client: bool = client
        self.server: bool = server
        self._ignore: tuple[tuple[str, int], ...] = ignore
        self.reset()

    def reset(self) -> None:
        from httpdbg.hooks.socket import TracerHTTP1
        from httpdbg.hooks.h2 import TracerHTTP2

        logger().info("HTTPRecords.reset")
        self.session: HTTPRecordsSessionInfo = HTTPRecordsSessionInfo()
        self.requests: dict[str, HTTPRecord] = {}
        self.requests_already_loaded = 0
        self.initiators: dict[str, Initiator] = {}
        self.current_initiator: Union[str, None] = None
        self.groups: dict[str, Group] = {}
        self.current_group: Union[str, None] = None
        self.current_tag: Union[str, None] = None
        self._tracerhttp1: TracerHTTP1 = TracerHTTP1(ignore=self.ignore)
        self._tracerhttp2: TracerHTTP2 = TracerHTTP2(ignore=self.ignore)

    @property
    def unread(self) -> int:
        return self.requests_already_loaded < len(self.requests)

    def __getitem__(self, item: int) -> HTTPRecord:
        return list(self.requests.values())[item]

    def __len__(self) -> int:
        return len(self.requests)

    def add_new_record_exception(
        self, initiator: Initiator, group: Group, url: str, exception: Exception
    ) -> HTTPRecord:
        from httpdbg.hooks.recordhttp1 import HTTP1Record

        if initiator.id not in self.initiators:
            self.initiators[initiator.id] = initiator
        new_record = HTTP1Record(initiator.id, group.id)
        new_record.url = url
        new_record.exception = exception
        self.requests[new_record.id] = new_record
        return new_record

    def add_initiator(self, initiator: Initiator):
        self.initiators[initiator.id] = initiator
        self.current_initiator = initiator.id

    def add_group(self, group: Group):
        self.groups[group.id] = group
        self.current_group = group.id

    @property
    def ignore(self) -> tuple[tuple[str, int], ...]:
        return self._ignore

    @ignore.setter
    def ignore(self, value) -> None:
        self._ignore = value
        self._tracerhttp1.ignore = value

    def _print_for_debug(self):
        for request in self.requests.values():
            print(f"+ {request.url}")
            print(f"  - initiator: {self.initiators[request.initiator_id].label}")
            print(f"  - group: {self.groups[request.group_id].label}")
