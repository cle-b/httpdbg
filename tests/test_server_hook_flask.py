import contextlib
import platform
import threading
import time

from flask import Flask
import pytest
import requests

from httpdbg.hooks.all import httprecord


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "Hello, World!"

    @app.route("/hello/<xxxx>/<yyyy>")
    def hello_custom(xxxx, yyyy):
        return f"{xxxx}, {yyyy}!"

    @app.route("/withclientrequest/<port>")
    def do_client_request(port):
        requests.get(f"http://localhost:{port}/")
        return "ok"

    @app.errorhandler(404)
    def not_found(e):
        return ("404-not found", 404)

    @app.route("/boum")
    def boum():
        1 / 0

    return app


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__()
        self.app = app
        self.host = "localhost"
        self.port = port
        self.server = None

    def run(self):
        from werkzeug.serving import make_server

        self.server = make_server(self.host, self.port, self.app)
        self.server.serve_forever()

    def shutdown(self):
        if self.server:
            self.server.shutdown()


@contextlib.contextmanager
def flaskapp(port):
    app = create_app()
    server_thread = ServerThread(app, port)
    server_thread.start()
    time.sleep(1)
    try:
        yield
    finally:
        server_thread.shutdown()
        server_thread.join(timeout=5)


@pytest.mark.server_requests
@pytest.mark.flask
def test_flask_endpoint(httpdbg_port):

    with httprecord(client=False, server=True) as records:
        with flaskapp(httpdbg_port):
            requests.get(f"http://localhost:{httpdbg_port}/")

    assert len(records) == 1
    record = records[0]
    group = records.groups[record.group_id]

    assert record.is_client is False
    assert record.response.content == b"Hello, World!"
    assert group.label == '@app.route("/")'
    assert "hello_world()" in group.full_label


@pytest.mark.server_requests
@pytest.mark.flask
def test_flask_endpoint_with_parameters(httpdbg_port):

    with httprecord(client=False, server=True) as records:
        with flaskapp(httpdbg_port):
            requests.get(f"http://localhost:{httpdbg_port}/hello/Salut/toi")

    assert len(records) == 1
    record = records[0]
    group = records.groups[record.group_id]

    assert record.is_client is False
    assert record.response.content == b"Salut, toi!"
    assert group.label == '@app.route("/hello/<xxxx>/<yyyy>")'
    full_label = group.full_label.replace(" ", "").replace("\t", "").replace("\n", "")
    assert 'hello_custom(xxxx="Salut",yyyy="toi",)' in full_label


@pytest.mark.server_requests
@pytest.mark.flask
def test_flask_not_found(httpdbg_port):

    with httprecord(client=False, server=True) as records:
        with flaskapp(httpdbg_port):
            requests.get(f"http://localhost:{httpdbg_port}/abcdef")

    assert len(records) == 1
    record = records[0]
    group = records.groups[record.group_id]

    assert record.is_client is False
    assert record.status_code == 404
    assert record.response.content == b"404-not found"
    assert group.label == "@app.errorhandler(404)"
    full_label = group.full_label.replace(" ", "").replace("\t", "").replace("\n", "")
    assert "not_found(e=" in full_label


@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="[#189] on Windows, the group label is empty in case of Internal Server Error in a Flask endpoint",
)
@pytest.mark.server_requests
@pytest.mark.flask
def test_flask_internal_server_error(httpdbg_port):

    with httprecord(client=False, server=True) as records:
        with flaskapp(httpdbg_port):
            requests.get(f"http://localhost:{httpdbg_port}/boum")

    assert len(records) == 1
    record = records[0]
    group = records.groups[record.group_id]

    assert record.is_client is False
    assert record.status_code == 500
    assert b"Internal Server Error" in record.response.content
    assert "def handle_exception" in group.label, records._print_for_debug()
    assert "division by zero" in group.full_label


@pytest.mark.server_requests
@pytest.mark.flask
def test_flask_client_request_in_endpoint(httpdbg_port, httpbin):

    with httprecord(
        client=True,
        server=True,
        ignore=[
            (httpbin.host, httpbin.port),
        ],
    ) as records:
        with flaskapp(httpdbg_port):
            requests.get(
                f"http://localhost:{httpdbg_port}/withclientrequest/{httpbin.port}"
            )

    assert len(records) == 3  # 2 + 1

    assert records[0].is_client is True  # the client request to /withclientrequest
    assert records[1].is_client is False  # the same request, received by the server
    assert records[2].is_client is True  # the request made inside the endpoint method
    assert records[0].group_id == records[1].group_id
    assert records[1].group_id == records[2].group_id
