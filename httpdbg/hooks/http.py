# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
from typing import Generator


from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_group
from httpdbg.records import HTTPRecords


def set_hook_for_http_server_handle_one_request(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):

        # the group label/full_label will be updated when the endpoint method will be called
        with httpdbg_group(records, "one request", "", updatable=True):
            ret = method(*args, **kwargs)

        return ret

    return hook


@contextmanager
def hook_http(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import http
        import http.server

        http.server.BaseHTTPRequestHandler.handle_one_request = decorate(
            records,
            http.server.BaseHTTPRequestHandler.handle_one_request,
            set_hook_for_http_server_handle_one_request,
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        http.server.BaseHTTPRequestHandler.handle_one_request = undecorate(
            http.server.BaseHTTPRequestHandler.handle_one_request
        )
