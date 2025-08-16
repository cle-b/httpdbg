# -*- coding: utf-8 -*-
from contextlib import contextmanager
from http.server import HTTPServer
import threading
from typing import Generator

from httpdbg.exception import HttpdbgException
from httpdbg.records import HTTPRecords
from httpdbg.webapp import HttpbgHTTPRequestHandler


@contextmanager
def httpdbg_srv(host: str, port: int) -> Generator[HTTPRecords, None, None]:
    server = None
    records = HTTPRecords()
    try:
        try:
            server = ServerThread(host, port, records)
            server.start()
        except Exception as ex_server_start:
            raise HttpdbgException(
                f"An issue occurred while starting the httpdbg web interface: [{str(ex_server_start)}]"
            )

        yield records

        server.shutdown()
    except Exception as ex:
        if server:
            server.shutdown()
        raise ex


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int, records: HTTPRecords) -> None:
        threading.Thread.__init__(self)
        self.port = port

        def http_request_handler(*args, **kwargs):
            HttpbgHTTPRequestHandler(records, *args, **kwargs)

        self.srv = HTTPServer((host, port), http_request_handler)
        records.ignore += (
            (str(self.srv.server_address[0]), self.srv.server_address[1]),
        )

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()
