# -*- coding: utf-8 -*-
from contextlib import contextmanager
from http.server import HTTPServer
import threading

from httpdbg.hook import set_hook, unset_hook
from httpdbg.webapp import HttpbgHTTPRequestHandler, httpdebugk7


@contextmanager
def httpdbg(port):
    with httpdbg_srv(port):
        with httpdbg_hook():
            yield


@contextmanager
def httpdbg_hook():
    try:
        set_hook(httpdebugk7)

        yield

        unset_hook()
    except Exception as ex:
        unset_hook()
        raise ex


@contextmanager
def httpdbg_srv(port):
    server = None
    try:
        server = ServerThread(port)
        server.start()

        yield

        server.shutdown()
    except Exception as ex:
        if server:
            server.shutdown()
        raise ex


class ServerThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.srv = HTTPServer(("localhost", port), HttpbgHTTPRequestHandler)

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()
