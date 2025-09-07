from collections.abc import Callable
from contextlib import contextmanager
import datetime
import typing
from typing import Generator

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.log import logger
from httpdbg.hooks.recordhttp1 import HTTP1Record
from httpdbg.records import HTTPRecords

if typing.TYPE_CHECKING:
    from httpdbg.hooks.socket import SocketRawData


# we use a proxy class to be able to override the write method
class TCPTransport:
    def __init__(self, transport, socketdata: "SocketRawData"):
        self.__httpdbg_original_transport = transport
        self.__httpdbg_socketdata = socketdata

    def write(self, buf):
        if self.__httpdbg_socketdata:
            if self.__httpdbg_socketdata.record:
                self.__httpdbg_socketdata.record.send_data(buf)
        return self.__httpdbg_original_transport.write(buf)

    def __getattr__(self, attr):
        return getattr(self.__httpdbg_original_transport, attr)


def set_hook_uvicorn_connection_made(records: HTTPRecords, method: Callable):

    def hook(self, transport):

        socketdata = records._tracerhttp1.get_socket_data(
            self, force_new=True, is_uvicorn=True
        )
        if socketdata:
            logger().debug(f"UVICORN - connection made - {socketdata}")
            return method(self, TCPTransport(transport, socketdata))
        else:
            # should not happen
            logger().debug("UVICORN - connection made - ignored")
            return method(self, transport)

    return hook


def set_hook_uvicorn_data_received(records: HTTPRecords, method: Callable):

    def hook(self, data):

        socketdata = records._tracerhttp1.get_socket_data(self)
        if socketdata:
            if socketdata.record:
                socketdata.record.receive_data(data)
            else:
                socketdata.rawdata += data
                http_detected = socketdata.http_detected()
                if http_detected:
                    logger().info("UVICORN - http detected")
                    with httpdbg_initiator(
                        records,
                        method,
                        self,
                        data,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTP1Record(
                            initiator.id,
                            group.id,
                            tbegin=socketdata.tbegin,
                            is_client=False,
                        )
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.receive_data(socketdata.rawdata)
                        if records.server:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._tracerhttp1.mark_as_not_a_http_request(self)

        return method(self, data)

    return hook


@contextmanager
def hook_uvicorn(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import uvicorn.protocols.http.httptools_impl

        uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.connection_made = (
            decorate(
                records,
                uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.connection_made,
                set_hook_uvicorn_connection_made,
            )
        )

        uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.data_received = (
            decorate(
                records,
                uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.data_received,
                set_hook_uvicorn_data_received,
            )
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.connection_made = (
            undecorate(
                uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.connection_made
            )
        )
        uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.data_received = (
            undecorate(
                uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.data_received
            )
        )
