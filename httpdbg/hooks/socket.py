# -*- coding: utf-8 -*-
import asyncio
import asyncio.proactor_events
from collections.abc import Callable
from contextlib import contextmanager
import datetime
import platform
import socket
import ssl
import sys
import traceback
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecords
from httpdbg.log import logger


# hook: socket.socket.__init__
# what: A new socket object is created.
# action: If an entry exists in the temporary raw socket storage list, it is removed.
def set_hook_for_socket_init(records: HTTPRecords, method: Callable):
    def hook(self, *args, **kwargs):
        records.del_socket_data(self)

        return method(self, *args, **kwargs)

    return hook


# hook: socket.socket.connect, ssl.SSLSocket.connect
# what: A connection to a remote socket is initiated.
# action: A new entry is added to the temporary raw socket storage list.
def set_hook_for_socket_connect(records: HTTPRecords, method: Callable):
    def hook(self, *args, **kwargs):
        tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        socketdata = records.get_socket_data(self, force_new=True)
        if socketdata:
            logger().info(
                f"CONNECT - self={self} id={id(self)} socketdata={socketdata} args={args} kwargs={kwargs}"
            )
        try:
            r = method(self, *args, **kwargs)
        except Exception as ex:
            if not isinstance(
                ex, (BlockingIOError, OSError)
            ):  # BlockingIOError for async, OSError for ipv6
                if records.client:
                    with httpdbg_initiator(
                        records, traceback.extract_stack(), method, *args, **kwargs
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                            records.add_new_record_exception(
                                initiator, group, "http:///", ex
                            )
            raise

        return r

    return hook


# hook: ssl.wrap_socket,
# what: Takes an instance sock of socket.socket, and returns an instance of ssl.SSLSocket.
# a subtype of socket.socket, which wraps the underlying socket in an SSL context.
# action: Link the socket and the sslsocket
def set_hook_for_ssl_wrap_socket(records: HTTPRecords, method: Callable):
    def hook(sock, *args, **kwargs):
        tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        try:
            sslsocket = method(sock, *args, **kwargs)
        except Exception as ex:
            if records.client:
                with httpdbg_initiator(
                    records, traceback.extract_stack(), method, *args, **kwargs
                ) as initiator_and_group:
                    initiator, group, is_new = initiator_and_group
                    if is_new:
                        initiator.tbegin = tbegin
                        group.tbegin = tbegin
                        records.add_new_record_exception(
                            initiator, group, "http:///", ex
                        )
            raise

        logger().info(
            f"WRAP_SOCKET - {type(sock)}={id(sock)} {type(sslsocket)}={id(sslsocket)}"
        )

        socketdata = records.move_socket_data(sslsocket, sock)
        if socketdata:
            logger().info(f"WRAP_SOCKET * - socketdata={socketdata}")

        return sslsocket

    return hook


# hook: ssl.SSLContext.wrap_socket
# what: Wrap an existing Python socket sock and return an instance of SSLContext.sslsocket_class (default SSLSocket).
# action: Link the socket and the sslsocket
def set_hook_for_sslcontext_wrap_socket(records: HTTPRecords, method: Callable):
    def hook(self, sock, *args, **kwargs):
        tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        try:
            sslsocket = method(self, sock, *args, **kwargs)
        except Exception as ex:
            if records.client:
                with httpdbg_initiator(
                    records, traceback.extract_stack(), method, *args, **kwargs
                ) as initiator_and_group:
                    initiator, group, is_new = initiator_and_group
                    if is_new:
                        initiator.tbegin = tbegin
                        group.tbegin = tbegin
                        records.add_new_record_exception(
                            initiator, group, "http:///", ex
                        )
            raise

        logger().info(
            f"WRAP_SOCKET (SSLContext) - {type(self)}={id(self)}  {type(sock)}={id(sock)} {type(sslsocket)}={id(sslsocket)}"
        )

        socketdata = records.move_socket_data(sslsocket, sock)
        if socketdata:
            logger().info(f"WRAP_SOCKET (SSLContext) * - socketdata={socketdata}")

        return sslsocket

    return hook


# hook: ssl.SSLContext.wrap_bio
# what: Wrap the BIO objects incoming and outgoing and return an instance of SSLContext.sslobject_class (default SSLObject).
# action: Record a new SocketRawData if necessary
def set_hook_for_socket_wrap_bio(records: HTTPRecords, method: Callable):
    def hook(self, *args, **kwargs):
        tbegin: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        try:
            sslobject = method(self, *args, **kwargs)
        except Exception as ex:
            if records.client:
                with httpdbg_initiator(
                    records, traceback.extract_stack(), method, *args, **kwargs
                ) as initiator_and_group:
                    initiator, group, is_new = initiator_and_group
                    if is_new:
                        initiator.tbegin = tbegin
                        group.tbegin = tbegin
                        records.add_new_record_exception(
                            initiator, group, "http:///", ex
                        )
            raise

        logger().info(
            f"WRAP_SOCKET_BIO - {type(self)}={id(self)} {type(sslobject)}={id(sslobject)}"
        )

        socketdata = records.get_socket_data(sslobject, self)
        if socketdata:
            logger().info(f"WRAP_SOCKET_BIO * - socketdata={socketdata}")

        return sslobject

    return hook


# hook: socket.socket.recv_into, ssl.SSLSocket.recv_into, asyncio.proactor_events._ProactorReadPipeTransport._data_received
# what: Receive up to nbytes bytes from the socket, storing the data into a buffer rather than creating a new bytestring.
# action: Append the data to an existing SocketRawData
def set_hook_for_socket_recv_into(records: HTTPRecords, method: Callable):
    def hook(self, buffer, *args, **kwargs):
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger().info(
                f"RECV_INTO - self={self} id={id(self)} socketdata={socketdata} args={args} kwargs={kwargs}"
            )

        nbytes = method(self, buffer, *args, **kwargs)

        if socketdata:
            if socketdata.record:
                logger().info(
                    f"RECV_INTO (after) - id={id(self)} buffer={(b''+buffer)[:20]}"
                )
                socketdata.record.receive_data(buffer[:nbytes])
            else:
                socketdata.rawdata += buffer[:nbytes]
                http_detected = socketdata.http_detected()
                if http_detected:
                    logger().info("RECV_INTO - http detected")
                    logger().info(
                        f"RECV_INTO (after) - id={id(self)} buffer={(b''+buffer)[:20]}"
                    )
                    with httpdbg_initiator(
                        records,
                        traceback.extract_stack(),
                        method,
                        self,
                        buffer,
                        *args,
                        **kwargs,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTPRecord(
                            tbegin=socketdata.tbegin, is_client=False
                        )
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.receive_data(socketdata.rawdata)
                        if records.server:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None

        return nbytes

    return hook


# hook: socket.socket.recv, ssl.SSLSocket.recv
# what: Receive data from the socket. The return value is a bytes object representing the data received.
# action: Append the data to an existing SocketRawData
def set_hook_for_socket_recv(records: HTTPRecords, method: Callable):
    def hook(self, bufsize, *args, **kwargs):
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger().info(
                f"RECV - self={self} id={id(self)} socketdata={socketdata} bufsize={bufsize} args={args} kwargs={kwargs}"
            )

        buffer = method(self, bufsize, *args, **kwargs)

        if socketdata:
            if socketdata.record:
                socketdata.record.receive_data(buffer)
            else:
                socketdata.rawdata += buffer
                http_detected = socketdata.http_detected()
                if http_detected:
                    logger().info("RECV - http detected")
                    with httpdbg_initiator(
                        records,
                        traceback.extract_stack(),
                        method,
                        self,
                        bufsize,
                        *args,
                        **kwargs,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTPRecord(
                            tbegin=socketdata.tbegin, is_client=False
                        )
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.receive_data(socketdata.rawdata)
                        if records.server:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None

        return buffer

    return hook


# hook: socket.socket.sendall
# what: Send data to the socket.
# action: Append the data to an existing SocketRawData. Check if this is an HTTP request.
# and record it if this is case, otherwise delete the temporay SocketRawData.
def set_hook_for_socket_sendall(records: HTTPRecords, method: Callable):
    def hook(self, data, *args, **kwargs):
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger().info(
                f"SENDALL - self={self} id={id(self)} socketdata={socketdata} data={(b''+bytes(data))[:20]} type={type(data)} args={args} kwargs={kwargs}"
            )
        if socketdata:
            if socketdata.record:
                socketdata.record.send_data(data)
            else:
                socketdata.rawdata += data
                http_detected = socketdata.http_detected()
                if http_detected:
                    logger().info("SENDALL - http detected")
                    with httpdbg_initiator(
                        records,
                        traceback.extract_stack(),
                        method,
                        self,
                        data,
                        *args,
                        **kwargs,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.send_data(socketdata.rawdata)
                        if records.client:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None

        return method(self, data, *args, **kwargs)

    return hook


# hook: socket.socket.send, ssl.SSLSocket.send, asyncio.proactor_events._ProactorBaseWritePipeTransport.write
# what: Send data to the socket.
# action: Append the data to an existing SocketRawData. Check if this is an HTTP request.
# and record it if this is case, otherwise delete the temporay SocketRawData.
def set_hook_for_socket_send(records: HTTPRecords, method: Callable):
    def hook(self, data, *args, **kwargs):
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger().info(
                f"SEND - self={self} id={id(self)} socketdata={socketdata} bytes={(b''+data)[:20]} args={args} kwargs={kwargs}"
            )

        size = method(self, data, *args, **kwargs)

        if socketdata:
            if socketdata.record:
                socketdata.record.send_data(data[:size])
            else:
                socketdata.rawdata += data[:size]
                http_detected = socketdata.http_detected()
                if http_detected:
                    with httpdbg_initiator(
                        records,
                        traceback.extract_stack(),
                        method,
                        self,
                        data,
                        *args,
                        **kwargs,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.send_data(socketdata.rawdata)
                        if records.client:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records._sockets[id(self)] = None
        return size

    return hook


# hook: asyncio.BaseEventLoop.create_connection
# what: Open a streaming transport connection to a given address specified by host and port.
# action: Link the socket and the sslsocket
def set_hook_for_asyncio_create_connection(records: HTTPRecords, method: Callable):
    async def hook(self, *args, **kwargs):
        logger().info(
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
                logger().info(
                    f"CREATE_CONNECTION - ssl_object ssl_object={ssl_object} ssl_objectid={id(ssl_object)} socketdata={socketdata}"
                )
        return r

    return hook


# hook: ssl.SSLObject.write
# what: Write buf to the SSL socket and return the number of bytes written.
# action: Append the data to an existing SocketRawData. Check if this is an HTTP request.
# and record it if this is case, otherwise delete the temporay SocketRawData.
def set_hook_for_sslobject_write(records: HTTPRecords, method: Callable):
    def hook(self, buf, *args, **kwargs):
        logger().info(f"WRITE - {type(self)}={id(self)} buf={(b'' + buf)[:20]}")
        socketdata = records.get_socket_data(self, request=True)
        if socketdata:
            logger().info(f"WRITE * - socketdata={socketdata}")

        size = method(self, buf, *args, **kwargs)

        if socketdata:
            if socketdata.record:
                socketdata.record.send_data(bytes(buf[:size]))
            else:
                socketdata.rawdata += bytes(buf[:size])
                http_detected = socketdata.http_detected()
                if http_detected:
                    with httpdbg_initiator(
                        records,
                        traceback.extract_stack(),
                        method,
                        self,
                        buf,
                        *args,
                        **kwargs,
                    ) as initiator_and_group:
                        initiator, group, is_new = initiator_and_group
                        if is_new:
                            tbegin = socketdata.tbegin - datetime.timedelta(
                                milliseconds=1
                            )
                            initiator.tbegin = tbegin
                            group.tbegin = tbegin
                        socketdata.record = HTTPRecord(tbegin=socketdata.tbegin)
                        socketdata.record.address = socketdata.address
                        socketdata.record.ssl = socketdata.ssl
                        socketdata.record.send_data(socketdata.rawdata)
                        if records.client:
                            records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records.sockets[id(self)] = None
        return size

    return hook


# hook: ssl.SSLObject.read
# what: Read up to len bytes of data from the SSL socket and return the result as a bytes instance.
# action: Append the data to an existing SocketRawData.
def set_hook_for_sslobject_read(records: HTTPRecords, method: Callable):
    def hook(self, *args, **kwargs):
        logger().info(f"READ - {type(self)}={id(self)}")
        socketdata = records.get_socket_data(self)
        if socketdata:
            logger().info(f"READ * - socketdata={socketdata}")

        r = method(self, *args, **kwargs)

        if socketdata and socketdata.record:
            allargs = getcallargs(method, self, *args, **kwargs)
            if allargs.get("buffer"):
                socketdata.record.receive_data(bytes(allargs.get("buffer"))[:r])
            else:
                socketdata.record.receive_data(bytes(r)[: allargs.get("len")])

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
        ssl.wrap_socket = decorate(  # type: ignore[attr-defined]
            records, ssl.wrap_socket, set_hook_for_ssl_wrap_socket  # type: ignore[attr-defined]
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
    if platform.system().lower() == "windows":
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
        ssl.wrap_socket = undecorate(ssl.wrap_socket)  # type: ignore[attr-defined]

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
    if platform.system().lower() == "windows":
        asyncio.proactor_events._ProactorReadPipeTransport._data_received = undecorate(  # type: ignore
            asyncio.proactor_events._ProactorReadPipeTransport._data_received  # type: ignore
        )
        asyncio.proactor_events._ProactorBaseWritePipeTransport.write = undecorate(
            asyncio.proactor_events._ProactorBaseWritePipeTransport.write
        )
