# -*- coding: utf-8 -*-
import code
import readline  # noqa: F401 enable the 'up arrow' history in the console
import threading

import vcr
from werkzeug.serving import make_server

from .vcrpy import HTTPDBGPersister
from .webapp import app, httpdebugconfig


def console_exit():
    raise SystemExit


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server("localhost", 5000, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


if __name__ == "__main__":

    server = ServerThread(app)
    server.start()

    my_vcr = vcr.VCR(
        serializer="yaml", cassette_library_dir="cassettes", record_mode="all"
    )
    my_vcr.register_persister(HTTPDBGPersister)

    print("httpdbg - recorded requests available at http://localhost:5000/ ")

    with my_vcr.use_cassette(
        path="cassettes", serializer="yaml", decode_compressed_response=True
    ) as k7:
        httpdebugconfig["k7"] = k7

        try:
            code.InteractiveConsole(locals={"exit": console_exit}).interact()
        except SystemExit:
            pass

    server.shutdown()
