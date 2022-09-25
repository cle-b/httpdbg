# -*- coding: utf-8 -*-
from contextlib import contextmanager
import threading

from werkzeug.serving import make_server

from httpdbg.hook import set_hook, unset_hook

from httpdbg.webapp import app, httpdebugk7


class ServerThread(threading.Thread):
    def __init__(self, port, app):
        threading.Thread.__init__(self)
        self.srv = make_server("localhost", port, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


@contextmanager
def httpdbg(port):
    try:
        server = ServerThread(port, app)
        server.start()

        set_hook(httpdebugk7)

        yield

        unset_hook()
    except Exception as ex:
        unset_hook()
        server.shutdown()
        raise ex
    finally:
        unset_hook()
        server.shutdown()
