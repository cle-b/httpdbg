# -*- coding: utf-8 -*-

import http.server
import socketserver
import threading

import pytest

PORT = 8045

# during the tests a http server is launched locally.
# the server always responds the text "from xxx" where xxx is the 'Host' header value


class FakeHTTPserver(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=UTF-8")
        self.end_headers()
        content = "from %s" % self.headers.get("Host")
        self.wfile.write(content.encode("utf-8"))


class Httpd(threading.Thread):
    def run(self):
        Handler = FakeHTTPserver
        Handler.timeout = 1
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer(("", PORT), Handler)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()


@pytest.fixture(scope="session", autouse=True)
def httpd():
    server = Httpd()
    server.start()
    yield
    server.stop()


@pytest.fixture(scope="session")
def httpdport():
    return PORT
