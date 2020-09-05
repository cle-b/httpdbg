# -*- coding: utf-8 -*-
from contextlib import contextmanager
import threading

import vcr
from werkzeug.serving import make_server

from .vcrpy import HTTPDBGPersister
from .webapp import app, httpdebugk7


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
def httpdbg(port=5000):
    try:
        server = ServerThread(port, app)
        server.start()

        my_vcr = vcr.VCR(
            serializer="yaml", cassette_library_dir="cassettes", record_mode="all"
        )
        my_vcr.register_persister(HTTPDBGPersister)

        with my_vcr.use_cassette(
            path="cassettes", serializer="yaml", decode_compressed_response=True
        ) as k7:
            httpdebugk7["k7"] = k7

            yield
    finally:
        server.shutdown()
