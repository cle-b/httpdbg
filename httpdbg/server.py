# -*- coding: utf-8 -*-
from contextlib import contextmanager
import threading

from werkzeug.serving import make_server

from httpdbg.hook import set_hook, unset_hook

from httpdbg.webapp import app, httpdebugk7


class ServerThread(threading.Thread):
    def __init__(self, port, app):
        threading.Thread.__init__(self)
        self.port = port
        self.srv = make_server("localhost", port, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


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
        server = ServerThread(port, app)
        server.start()

        yield

        server.shutdown()
    except Exception as ex:
        if server:
            server.shutdown()
        raise ex
