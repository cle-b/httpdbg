# -*- coding: utf-8 -*-
from contextlib import contextmanager
from http.server import HTTPServer
import threading
from typing import Generator

from httpdbg.records import HTTPRecords
from httpdbg.webapp import HttpbgHTTPRequestHandler


@contextmanager
def httpdbg_srv(port: int) -> Generator[HTTPRecords, None, None]:
    server = None
    records = HTTPRecords()
    try:
        server = ServerThread(port, records)
        server.start()

        yield records

        server.shutdown()
    except Exception as ex:
        if server:
            server.shutdown()
        raise ex


class ServerThread(threading.Thread):
    def __init__(self, port: int, records: HTTPRecords) -> None:
        threading.Thread.__init__(self)
        self.port = port

        def http_request_handler(*args, **kwargs):
            HttpbgHTTPRequestHandler(records, *args, **kwargs)

        self.srv = HTTPServer(("localhost", port), http_request_handler)

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()
