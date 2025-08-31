import contextlib
import platform
import threading
import time

import pytest
import requests
import uvicorn

from httpdbg.hooks.all import httprecord


@contextlib.contextmanager
def fastapi_app(port):
    try:
        config = uvicorn.Config("tests.demo_fastapi:app", port=port, log_level="debug")
        server = uvicorn.Server(config)

        thread = threading.Thread(target=server.run)
        thread.start()

        time.sleep(5)
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=5)


# For some reason I don't yet understand, it looks like the hook for fastapi.routing.get_request_handler
# is applied only once when starting multiple FastAPI apps sequentially.
@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="on windows, the server requests are recorded twice for fastapi",
)
@pytest.mark.server_requests
@pytest.mark.fastapi
def test_fastapi_endpoint(httpdbg_port):

    with httprecord(client=False, server=True) as records:
        with fastapi_app(httpdbg_port):
            requests.get(f"http://localhost:{httpdbg_port}/")

            # endpoint no parameters
            assert len(records) == 1, records._print_for_debug()
            record = records[0]
            group = records.groups[record.group_id]

            assert record.is_client is False
            assert record.response.content == b'"Hello, World!"'
            assert group.label == '@app.get("/")'
            assert "hello_world()" in group.full_label

            records.reset()

            # endpoint with parameters

            requests.get(f"http://localhost:{httpdbg_port}/items/123")

            assert len(records) == 1, records._print_for_debug()
            record = records[0]
            group = records.groups[record.group_id]

            assert record.is_client is False
            assert record.response.content == b'{"item_id":123,"q":null}'
            assert group.label == '@app.get("/items/{item_id}")'
            full_label = (
                group.full_label.replace(" ", "").replace("\t", "").replace("\n", "")
            )
            assert "get_item(item_id=123,q=None,)" in full_label

            records.reset()

            # http error
            requests.get(f"http://localhost:{httpdbg_port}/items/456")

            assert len(records) == 1
            record = records[0]
            group = records.groups[record.group_id]

            assert record.is_client is False
            assert record.status_code == 456
            assert record.response.content == b'{"detail":"custom exception"}'
            assert group.label == '@app.get("/items/{item_id}")'
            full_label = (
                group.full_label.replace(" ", "").replace("\t", "").replace("\n", "")
            )
            assert "get_item(item_id=456,q=None,)" in full_label


@pytest.mark.xfail(
    platform.system().lower() == "windows",
    reason="[#188] on windows, the server requests are recorded twice for fastapi",
)
@pytest.mark.server_requests
@pytest.mark.fastapi
def test_fastapi_client_request_in_endpoint(httpdbg_port, httpbin):

    with httprecord(
        client=True,
        server=True,
        ignore=[
            (httpbin.host, httpbin.port),
        ],
    ) as records:
        with fastapi_app(httpdbg_port):
            requests.post(
                f"http://localhost:{httpdbg_port}/withclientrequest",
                json={"port": httpbin.port},
            )

    assert len(records) == 3  # 2 + 1

    assert records[0].is_client is True  # the client request to /withclientrequest
    assert records[1].is_client is False  # the same request, received by the server
    assert records[2].is_client is True  # the request made inside the endpoint method
    assert records[0].group_id == records[1].group_id
    assert records[1].group_id == records[2].group_id

    assert records[2].url == f"http://localhost:{httpbin.port}/"
