# -*- coding: utf-8 -*-
import asyncio
import asyncio.proactor_events
from contextlib import contextmanager
import platform
import socket
import ssl
import sys
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecords
from httpdbg.utils import logger


def set_hook_for_socket_init(records, method):
    def hook(self, *args, **kwargs):
        records.del_socket_data(self)

        return method(self, *args, **kwargs)

    return hook


def set_hook_for_socket_connect(records, method):
    def hook(self, address):
        socketdata = records.get_socket_data(self, force_new=True)
        if socketdata:
            logger.info(
                f"CONNECT - self={self} id={id(self)} socketdata={socketdata} address={address}"
            )

        try:
            r = method(self, address)
        except Exception as ex:
            if not isinstance(
                ex, (BlockingIOError, OSError)
            ):  # BlockingIOError for async, OSError for ipv6
                record = HTTPRecord()
                record.initiator = records.get_initiator()

                record.exception = ex

                records.requests[record.id] = record

            raise

        return r

    return hook


def set_hook_for_ssl_wrap_socket(records, method):
    def hook(sock, *args, **kwargs):
        try:
            sslsocket = method(sock, *args, **kwargs)
        except Exception as ex:
            record = HTTPRecord()

            record.initiator = records.get_initiator()
            record.exception = ex

            records.requests[record.id] = record

            raise

        logger.info(
            f"WRAP_SOCKET - {type(sock)}={id(sock)} {type(sslsocket)}={id(sslsocket)}"
        )

        socketdata = records.move_socket_data(sslsocket, sock)
        if socketdata:
            logger.info(f"WRAP_SOCKET * - socketdata={socketdata}")

        return sslsocket

    return hook


def set_hook_for_sslcontext_wrap_socket(records, method):
    def hook(self, sock, *args, **kwargs):
        try:
            sslsocket = method(self, sock, *args, **kwargs)
        except Exception as ex:
            record = HTTPRecord()

            record.initiator = records.get_initiator()
            record.exception = ex

            records.requests[record.id] = record

            raise

        logger.info(
            f"WRAP_SOCKET (SSLContext) - {type(self)}={id(self)}  {type(sock)}={id(sock)} {type(sslsocket)}={id(sslsocket)}"
        )

        socketdata = records.move_socket_data(sslsocket, sock)
        if socketdata:
            logger.info(f"WRAP_SOCKET (SSLContext) * - socketdata={socketdata}")

        return sslsocket

    return hook


def set_hook_for_socket_wrap_bio(records, method):
    def hook(self, *args, **kwargs):
        try:
            sslobject = method(self, *args, **kwargs)
        except Exception as ex:
            record = HTTPRecord()
            record.initiator = records.get_initiator()

            record.exception = ex

            records.requests[record.id] = record

            raise

        logger.info(
            f"WRAP_SOCKET_BIO - {type(self)}={id(self)} {type(sslobject)}={id(sslobject)}"
        )

        socketdata = records.get_socket_data(sslobject, self)
        if socketdata:
            logger.info(f"WRAP_SOCKET_BIO * - socketdata={socketdata}")

        return sslobject

    return hook


def set_hook_for_socket_recv_into(records, method):
    def hook(self, buffer, *args, **kwargs):
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger.info(
                f"RECV_INTO - self={self} id={id(self)} socketdata={socketdata} args={args} kwargs={kwargs}"
            )

        try:
            nbytes = method(self, buffer, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

        if socketdata and socketdata.record:
            logger.info(f"RECV_INTO (after) - id={id(self)} buffer={(b''+buffer)[:20]}")
            socketdata.record.response.rawdata += buffer[:nbytes]

        return nbytes

    return hook


def set_hook_for_socket_recv(records, method):
    def hook(self, bufsize, *args, **kwargs):
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger.info(
                f"RECV - self={self} id={id(self)} socketdata={socketdata} bufsize={bufsize} args={args} kwargs={kwargs}"
            )

        try:
            buffer = method(self, bufsize, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

        if socketdata and socketdata.record:
            socketdata.record.response.rawdata += buffer

        return buffer

    return hook


def set_hook_for_socket_sendall(records, method):
    def hook(self, bytes, *args, **kwargs):
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger.info(
                f"SENDALL - self={self} id={id(self)} socketdata={socketdata} bytes={(b''+bytes)[:20]} type={type(bytes)} len={len(bytes)} args={args} kwargs={kwargs}"
            )

        if socketdata:
            if socketdata.record:
                socketdata.record.request.rawdata += bytes
            else:
                socketdata.rawdata += bytes
                http_detected = socketdata.http_detected()
                if http_detected:
                    logger.info("SENDALL - http detected")
                    socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                    socketdata.record.initiator = records.get_initiator()
                    socketdata.record.address = socketdata.address
                    socketdata.record.ssl = socketdata.ssl
                    socketdata.record.request.rawdata = socketdata.rawdata
                    records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None

        try:
            return method(self, bytes, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

    return hook


def set_hook_for_socket_send(records, method):
    def hook(self, bytes, *args, **kwargs):
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger.info(
                f"SEND - self={self} id={id(self)} socketdata={socketdata} bytes={(b''+bytes)[:20]} args={args} kwargs={kwargs}"
            )

        try:
            size = method(self, bytes, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

        if socketdata:
            if socketdata.record:
                socketdata.record.request.rawdata += bytes[:size]
            else:
                socketdata.rawdata += bytes[:size]
                http_detected = socketdata.http_detected()
                if http_detected:
                    socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                    socketdata.record.initiator = records.get_initiator()
                    socketdata.record.address = socketdata.address
                    socketdata.record.ssl = socketdata.ssl
                    socketdata.record.request.rawdata = socketdata.rawdata
                    records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None
        return size

    return hook


def set_hook_for_asyncio_create_connection(records, method):
    async def hook(self, *args, **kwargs):
        logger.info(
            f"CREATE_CONNECTION - self={self} id={id(self)} args={args} kwargs={kwargs}"
        )
        r = await method(self, *args, **kwargs)

        transport = r[0]
        sock = transport.get_extra_info("socket")
        if sock:
            ssl_object = transport.get_extra_info("ssl_object")
            if ssl_object:
                socketdata = records.get_socket_data(
                    ssl_object, sock, force_new=True
                )  # to link the cnx info to the sslobject
                logger.info(
                    f"CREATE_CONNECTION - ssl_object ssl_object={ssl_object} ssl_objectid={id(ssl_object)} socketdata={socketdata}"
                )
        return r

    return hook


def set_hook_for_sslobject_write(records, method):
    def hook(self, buf, *args, **kwargs):
        logger.info(f"WRITE - {type(self)}={id(self)} buf={(b'' + buf)[:20]}")
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger.info(f"WRITE * - socketdata={socketdata}")

        try:
            size = method(self, buf, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

        if socketdata:
            if socketdata.record:
                socketdata.record.request.rawdata += bytes(buf[:size])
            else:
                socketdata.rawdata += bytes(buf[:size])
                http_detected = socketdata.http_detected()
                if http_detected:
                    socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                    socketdata.record.initiator = records.get_initiator()
                    socketdata.record.address = socketdata.address
                    socketdata.record.ssl = socketdata.ssl
                    socketdata.record.request.rawdata = socketdata.rawdata
                    records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records.sockets[id(self)] = None
        return size

    return hook


def set_hook_for_sslobject_read(records, method):
    def hook(self, *args, **kwargs):
        logger.info(f"READ - {type(self)}={id(self)}")
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger.info(f"READ * - socketdata={socketdata}")

        try:
            r = method(self, *args, **kwargs)
        except Exception as ex:
            if not isinstance(ex, ssl.SSLWantReadError):
                if socketdata and socketdata.record:
                    socketdata.record.exception = ex
            raise

        if socketdata and socketdata.record:
            allargs = getcallargs(method, self, *args, **kwargs)
            if allargs.get("buffer"):
                socketdata.record.response.rawdata += bytes(allargs.get("buffer"))[:r]
            else:
                socketdata.record.response.rawdata += bytes(r)[: allargs.get("len")]

        return r

    return hook


@contextmanager
def hook_socket(records: HTTPRecords) -> Generator[None, None, None]:
    socket.socket.__init__ = decorate(
        records, socket.socket.__init__, set_hook_for_socket_init
    )

    socket.socket.connect = decorate(
        records, socket.socket.connect, set_hook_for_socket_connect
    )
    socket.socket.recv_into = decorate(
        records, socket.socket.recv_into, set_hook_for_socket_recv_into
    )
    socket.socket.recv = decorate(records, socket.socket.recv, set_hook_for_socket_recv)
    socket.socket.sendall = decorate(
        records, socket.socket.sendall, set_hook_for_socket_sendall
    )
    socket.socket.send = decorate(records, socket.socket.send, set_hook_for_socket_send)

    if (sys.version_info.major == 3) and (sys.version_info.minor < 12):
        ssl.wrap_socket = decorate(
            records, ssl.wrap_socket, set_hook_for_ssl_wrap_socket
        )

    ssl.SSLContext.wrap_socket = decorate(
        records, ssl.SSLContext.wrap_socket, set_hook_for_sslcontext_wrap_socket
    )
    ssl.SSLContext.wrap_bio = decorate(
        records, ssl.SSLContext.wrap_bio, set_hook_for_socket_wrap_bio
    )

    ssl.SSLSocket.connect = decorate(
        records, ssl.SSLSocket.connect, set_hook_for_socket_connect
    )
    ssl.SSLSocket.recv_into = decorate(
        records, ssl.SSLSocket.recv_into, set_hook_for_socket_recv_into
    )
    ssl.SSLSocket.recv = decorate(records, ssl.SSLSocket.recv, set_hook_for_socket_recv)
    # ssl.SSLSocket.sendall = decorate(
    #     records, ssl.SSLSocket.sendall, set_hook_for_socket_sendall
    # )
    ssl.SSLSocket.send = decorate(records, ssl.SSLSocket.send, set_hook_for_socket_send)

    # for aiohttp
    ssl.SSLObject.write = decorate(
        records, ssl.SSLObject.write, set_hook_for_sslobject_write
    )
    ssl.SSLObject.read = decorate(
        records, ssl.SSLObject.read, set_hook_for_sslobject_read
    )
    asyncio.BaseEventLoop.create_connection = decorate(
        records,
        asyncio.BaseEventLoop.create_connection,
        set_hook_for_asyncio_create_connection,
    )

    # only for async HTTP requests (not HTTPS) on Windows
    if (platform.system().lower() == "windows") and (sys.version_info >= (3, 7)):
        asyncio.proactor_events._ProactorReadPipeTransport._data_received = decorate(  # type: ignore
            records,
            asyncio.proactor_events._ProactorReadPipeTransport._data_received,  # type: ignore
            set_hook_for_socket_recv_into,
        )
        asyncio.proactor_events._ProactorBaseWritePipeTransport.write = decorate(
            records,
            asyncio.proactor_events._ProactorBaseWritePipeTransport.write,
            set_hook_for_socket_send,
        )

    yield

    socket.socket.__init__ = undecorate(socket.socket.__init__)

    socket.socket.connect = undecorate(socket.socket.connect)
    socket.socket.recv_into = undecorate(socket.socket.recv_into)
    socket.socket.recv = undecorate(socket.socket.recv)
    socket.socket.sendall = undecorate(socket.socket.sendall)
    socket.socket.send = undecorate(socket.socket.send)

    if (sys.version_info.major == 3) and (sys.version_info.minor < 12):
        ssl.wrap_socket = undecorate(ssl.wrap_socket)

    ssl.SSLContext.wrap_socket = undecorate(ssl.SSLContext.wrap_socket)
    ssl.SSLContext.wrap_bio = undecorate(ssl.SSLContext.wrap_bio)

    ssl.SSLSocket.connect = undecorate(ssl.SSLSocket.connect)
    ssl.SSLSocket.recv_into = undecorate(ssl.SSLSocket.recv_into)
    ssl.SSLSocket.recv = undecorate(ssl.SSLSocket.recv)
    # ssl.SSLSocket.sendall = undecorate(ssl.SSLSocket.sendall)
    ssl.SSLSocket.send = undecorate(ssl.SSLSocket.send)

    # for aiohttp / async httpx
    ssl.SSLObject.write = undecorate(ssl.SSLObject.write)
    ssl.SSLObject.read = undecorate(ssl.SSLObject.read)
    asyncio.BaseEventLoop.create_connection = undecorate(
        asyncio.BaseEventLoop.create_connection
    )

    # only for async HTTP requests (not HTTPS) on Windows
    if (platform.system().lower() == "windows") and (sys.version_info >= (3, 7)):
        asyncio.proactor_events._ProactorReadPipeTransport._data_received = undecorate(  # type: ignore
            asyncio.proactor_events._ProactorReadPipeTransport._data_received  # type: ignore
        )
        asyncio.proactor_events._ProactorBaseWritePipeTransport.write = undecorate(
            asyncio.proactor_events._ProactorBaseWritePipeTransport.write
        )
