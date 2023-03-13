# -*- coding: utf-8 -*-
import asyncio
from contextlib import contextmanager
import socket
import ssl

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import get_initiator
from httpdbg.records import HTTPRecord


class SocketRawData(object):
    def __init__(self, id, address, ssl):
        self.id = id
        self.address = address
        self.ssl = ssl
        self.rawdata = bytes()
        self.record = None

    def http_detected(self):
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


def set_hook_for_socket_connect(records, method):
    def hook(self, address):
        records.sockets[id(self)] = SocketRawData(
            id(self), address, isinstance(self, ssl.SSLSocket)
        )

        try:
            r = method(self, address)
        except Exception as ex:
            if not isinstance(ex, BlockingIOError):  # for async
                record = HTTPRecord()
                record.initiator = get_initiator(records._initiators)

                record.exception = ex

                records.requests[record.id] = record

            raise

        return r

    return hook


def set_hook_for_socket_wrap_socket(records, method):
    def hook(self, sock, *args, **kwargs):
        try:
            sslsocket = method(self, sock, *args, **kwargs)
        except Exception as ex:
            record = HTTPRecord()
            record.initiator = get_initiator(records._initiators)

            record.exception = ex

            records.requests[record.id] = record

            raise

        socketdata = records.sockets.get(id(sock))

        if socketdata:
            socketdata.ssl = True
            records.sockets[id(sslsocket)] = socketdata

        return sslsocket

    return hook


def set_hook_for_socket_wrap_bio(records, method):
    def hook(self, *args, **kwargs):
        try:
            sslobject = method(self, *args, **kwargs)
        except Exception as ex:
            record = HTTPRecord()
            record.initiator = get_initiator(records._initiators)

            record.exception = ex

            records.requests[record.id] = record

            raise

        socketdata = records.sockets.get(id(self))

        if socketdata:
            socketdata.ssl = True
            records.sockets[id(sslobject)] = socketdata
            records.sockets[id(self)] = None

        return sslobject

    return hook


def set_hook_for_socket_recv_into(records, method):
    def hook(self, buffer, *args, **kwargs):
        socketdata = records.sockets.get(id(self))

        try:
            nbytes = method(self, buffer, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

        if socketdata and socketdata.record:
            socketdata.record.response.rawdata += buffer[:nbytes]

        return nbytes

    return hook


def set_hook_for_socket_recv(records, method):
    def hook(self, bufsize, *args, **kwargs):
        socketdata = records.sockets.get(id(self))

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
        socketdata = records.sockets.get(id(self))

        if socketdata:
            if socketdata.record:
                socketdata.record.request.rawdata += bytes
            else:
                socketdata.rawdata += bytes
                http_detected = socketdata.http_detected()
                if http_detected:
                    socketdata.record = HTTPRecord()
                    socketdata.record.initiator = get_initiator(records._initiators)
                    socketdata.record.address = socketdata.address
                    socketdata.record.ssl = socketdata.ssl
                    socketdata.record.request.rawdata = socketdata.rawdata
                    records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records.sockets[id(self)] = None

        try:
            return method(self, bytes, *args, **kwargs)
        except Exception as ex:
            if socketdata and socketdata.record:
                socketdata.record.exception = ex
            raise

    return hook


def set_hook_for_socket_send(records, method):
    def hook(self, bytes, *args, **kwargs):
        socketdata = records.sockets.get(id(self))

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
                    socketdata.record = HTTPRecord()
                    socketdata.record.initiator = get_initiator(records._initiators)
                    socketdata.record.address = socketdata.address
                    socketdata.record.ssl = socketdata.ssl
                    socketdata.record.request.rawdata = socketdata.rawdata
                    records.requests[socketdata.record.id] = socketdata.record
                elif http_detected is False:  # if None, there is nothing to do
                    records.sockets[id(self)] = None
        return size

    return hook


def set_hook_for_asyncio_create_connection(records, method):
    def hook(self, *args, **kwargs):
        allargs = getcallargs(method, self, *args, **kwargs)

        if allargs.get("ssl"):
            if allargs.get("sock") and records.sockets.get(id(allargs.get("sock"))):
                records.sockets[id(allargs.get("ssl"))] = records.sockets[
                    id(allargs.get("sock"))
                ]
            elif allargs.get("host") and allargs.get("port"):
                records.sockets[id(allargs.get("ssl"))] = SocketRawData(
                    id(allargs.get("ssl")),
                    (allargs.get("host"), allargs.get("port")),
                    True,
                )

        return method(self, *args, **kwargs)

    return hook


def set_hook_for_sslobject_write(records, method):
    def hook(self, buf, *args, **kwargs):
        socketdata = records.sockets.get(id(self))

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
                    socketdata.record = HTTPRecord()
                    socketdata.record.initiator = get_initiator(records._initiators)
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
        allargs = getcallargs(method, self, *args, **kwargs)

        socketdata = records.sockets.get(id(self))

        try:
            r = method(self, *args, **kwargs)
        except Exception as ex:
            if not isinstance(ex, ssl.SSLWantReadError):
                if socketdata and socketdata.record:
                    socketdata.record.exception = ex
            raise

        if socketdata and socketdata.record:
            if allargs.get("buffer"):
                socketdata.record.response.rawdata += bytes(allargs.get("buffer"))[:r]
            else:
                socketdata.record.response.rawdata += bytes(r)[: allargs.get("len")]

        return r

    return hook


@contextmanager
def hook_socket(records):
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

    ssl.wrap_socket = decorate(
        records, ssl.wrap_socket, set_hook_for_socket_wrap_socket
    )
    ssl.SSLContext.wrap_socket = decorate(
        records, ssl.SSLContext.wrap_socket, set_hook_for_socket_wrap_socket
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
    ssl.SSLSocket.sendall = decorate(
        records, ssl.SSLSocket.sendall, set_hook_for_socket_sendall
    )
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

    yield

    socket.socket.connect = undecorate(socket.socket.connect)
    socket.socket.recv_into = undecorate(socket.socket.recv_into)
    socket.socket.recv = undecorate(socket.socket.recv)
    socket.socket.sendall = undecorate(socket.socket.sendall)
    socket.socket.send = undecorate(socket.socket.send)

    ssl.wrap_socket = undecorate(ssl.wrap_socket)
    ssl.SSLContext.wrap_socket = undecorate(ssl.SSLContext.wrap_socket)
    ssl.SSLContext.wrap_bio = undecorate(ssl.SSLContext.wrap_bio)

    ssl.SSLSocket.connect = undecorate(ssl.SSLSocket.connect)
    ssl.SSLSocket.recv_into = undecorate(ssl.SSLSocket.recv_into)
    ssl.SSLSocket.recv = undecorate(ssl.SSLSocket.recv)
    ssl.SSLSocket.sendall = undecorate(ssl.SSLSocket.sendall)
    ssl.SSLSocket.send = undecorate(ssl.SSLSocket.send)

    # for aiohttp
    ssl.SSLObject.write = undecorate(ssl.SSLObject.write)
    ssl.SSLObject.read = undecorate(ssl.SSLObject.read)
    asyncio.BaseEventLoop.create_connection = undecorate(
        asyncio.BaseEventLoop.create_connection
    )
