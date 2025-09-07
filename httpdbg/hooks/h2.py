from collections.abc import Callable
from contextlib import contextmanager
import random
from typing import Generator
from typing import Union

from httpdbg.hooks.recordhttp2 import HTTP2Record
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.log import logger
from httpdbg.records import HTTPRecords


class TracerHTTP2:

    def __init__(
        self,
        ignore: tuple[tuple[str, int], ...] = (),
    ):
        self.sockets: dict[str, HTTP2Record] = dict()
        self.ignore: tuple[tuple[str, int], ...] = ignore

    def send_headers(
        self,
        initiator_id: str,
        group_id: str,
        socket_id: int,
        stream_id: int,
        headers: list[tuple[bytes, bytes]],
    ) -> HTTP2Record:

        if f"{socket_id}-{stream_id}" in self.sockets:
            record = self.sockets[f"{socket_id}-{stream_id}"]
            if record.is_client:
                # this is a new request: we "close" the previous one
                self.sockets.pop(f"{socket_id}-{stream_id}")

                record = HTTP2Record(initiator_id, group_id)
                record.request.headers = headers
                self.sockets[f"{socket_id}-{stream_id}"] = record
            else:
                record.response.headers = headers
        else:
            record = HTTP2Record(initiator_id, group_id)
            record.request.headers = headers
            self.sockets[f"{socket_id}-{stream_id}"] = record

        return record

    def send_data(
        self,
        socket_id: int,
        stream_id: int,
        data: bytes,
    ):
        record = self.sockets.get(f"{socket_id}-{stream_id}")
        if record:
            record.send_data(data)

    def receive_headers(
        self,
        initiator_id: str,
        group_id: str,
        socket_id: int,
        stream_id: int,
        headers: list[tuple[bytes, bytes]],
        is_client: bool = True,
    ) -> Union[HTTP2Record, None]:
        record = None
        if not is_client:
            if f"{socket_id}-{stream_id}" in self.sockets:
                # this is a new request received by the server: we "close" the previous one
                self.sockets.pop(f"{socket_id}-{stream_id}")
            record = HTTP2Record(initiator_id, group_id, is_client=False)
            record.request.headers = headers
            self.sockets[f"{socket_id}-{stream_id}"] = record
        else:
            if f"{socket_id}-{stream_id}" in self.sockets:
                record = self.sockets[f"{socket_id}-{stream_id}"]
                record.response.headers = headers
        return record

    def receive_data(
        self,
        socket_id: int,
        stream_id: int,
        data: bytes,
    ):
        record = self.sockets.get(f"{socket_id}-{stream_id}")
        if record:
            record.receive_data(data)


def set_hook_for_h2_send_headers(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)
        self = callargs.get("self")
        stream_id = callargs.get("stream_id")
        headers = callargs.get("headers")

        with httpdbg_initiator(records, method, *args, **kwargs) as initiator_and_group:
            initiator, group, _ = initiator_and_group
            if all(x is not None for x in (self, stream_id, headers)):
                logger().debug(
                    f"H2 send_headers - self={id(self)} steam_id={stream_id} headers={headers}"
                )
                record = records._tracerhttp2.send_headers(
                    initiator.id, group.id, id(self), stream_id, headers
                )
                if record.is_client and records.client:
                    records.requests[record.id] = record
            ret = method(*args, **kwargs)
        return ret

    return hook


def set_hook_for_h2_send_data(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)
        self = callargs.get("self")
        stream_id = callargs.get("stream_id")
        data = callargs.get("data")

        with httpdbg_initiator(records, method, *args, **kwargs):
            if all(x is not None for x in (self, stream_id, data)):
                logger().debug(
                    f"H2 send_data - self={id(self)} steam_id={stream_id} data={data[:20]!r}"
                )
                records._tracerhttp2.send_data(id(self), stream_id, data)
            ret = method(*args, **kwargs)
        return ret

    return hook


def set_hook_for_h2_receive_data(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)
        self = callargs.get("self")

        with httpdbg_initiator(records, method, *args, **kwargs) as initiator_and_group:
            initiator, group, _ = initiator_and_group
            ret = method(*args, **kwargs)

        for event in ret:
            import h2.events

            if isinstance(event, h2.events.RequestReceived):
                stream_id = event.stream_id
                headers = event.headers
                if all(x is not None for x in (self, stream_id, headers)):
                    logger().debug(
                        f"H2 receive_data headers RequestReceived {random.random()} - self={id(self)} steam_id={stream_id} headers={headers}"
                    )
                    record = records._tracerhttp2.receive_headers(
                        initiator.id,
                        group.id,
                        id(self),
                        stream_id,
                        headers,
                        is_client=False,
                    )
                    if record and (record.is_client is False) and records.server:
                        records.requests[record.id] = record

            elif isinstance(event, h2.events.ResponseReceived):
                stream_id = event.stream_id
                headers = event.headers
                if all(x is not None for x in (self, stream_id, headers)):
                    logger().debug(
                        f"H2 receive_data headers ResponseReceived {random.random()} - self={id(self)} steam_id={stream_id} headers={headers}"
                    )
                    records._tracerhttp2.receive_headers(
                        initiator.id, group.id, id(self), stream_id, headers
                    )

            elif isinstance(event, h2.events.DataReceived):
                stream_id = event.stream_id
                data = event.data
                if all(x is not None for x in (self, stream_id, data)):
                    logger().debug(
                        f"H2 receive_data data - self={id(self)} steam_id={stream_id} data={data[:20]!r}"
                    )
                    records._tracerhttp2.receive_data(id(self), stream_id, data)

        return ret

    return hook


@contextmanager
def hook_h2(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import h2.connection

        h2.connection.H2Connection.send_headers = decorate(records, h2.connection.H2Connection.send_headers, set_hook_for_h2_send_headers)  # type: ignore[arg-type]
        h2.connection.H2Connection.send_data = decorate(records, h2.connection.H2Connection.send_data, set_hook_for_h2_send_data)  # type: ignore[arg-type]
        h2.connection.H2Connection.receive_data = decorate(records, h2.connection.H2Connection.receive_data, set_hook_for_h2_receive_data)  # type: ignore[arg-type]

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        h2.connection.H2Connection.send_headers = undecorate(h2.connection.H2Connection.send_headers)  # type: ignore[arg-type]
        h2.connection.H2Connection.send_data = undecorate(h2.connection.H2Connection.send_data)  # type: ignore[arg-type]
        h2.connection.H2Connection.receive_data = undecorate(h2.connection.H2Connection.receive_data)  # type: ignore[arg-type]
