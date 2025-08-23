# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import functools
from functools import wraps
from typing import Generator

import datetime

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_endpoint
from httpdbg.records import HTTPRecords


# decorate the function decorated by @app.get; @app.post etc.
def set_hook_fastapi_endpoint(records: HTTPRecords, method: Callable):

    @wraps(method)
    def hook(*args, **kwargs):

        with httpdbg_endpoint(
            records,
            method,
            *args,
            **kwargs,
        ):
            ret = method(*args, **kwargs)
        return ret

    return hook


def set_hook_fastapi_apirouter_add_api_route(
    records: HTTPRecords,
    method: Callable,
    already_mapped: dict[Callable, Callable],
):

    @wraps(method)
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)

        param = "endpoint"

        if param in callargs:
            original_view_func = callargs[param]
            if original_view_func not in already_mapped:
                callargs[param] = decorate(
                    records, callargs[param], set_hook_fastapi_endpoint
                )
                already_mapped[original_view_func] = callargs[param]
            else:
                callargs[param] = already_mapped[original_view_func]

            args = tuple(
                callargs[param] if x == original_view_func else x for x in args
            )
            if param in kwargs:
                kwargs[param] = callargs[param]

        return method(*args, **kwargs)

    return hook


# decorate the "app" returned by fastapi.routing.get_request_handler to link the socketdata and the endpoint group
def set_hook_fastapi_app(records: HTTPRecords, method: Callable):

    @wraps(method)
    async def hook(*args, **kwargs):

        socketdata_id = None

        callargs = getcallargs(method, *args, **kwargs)

        if "request" in callargs:
            if hasattr(callargs["request"], "__httpdbg_socketdata_id"):
                socketdata_id = callargs["request"].__httpdbg_socketdata_id

        with httpdbg_endpoint(
            records,
            method,
            *args,
            **kwargs,
        ) as group:
            if group and socketdata_id:
                sock = records._tracerhttp1.sockets.get(socketdata_id)
                if (sock is not None) and (sock.record is not None):
                    record = records.groups.get(group.id)
                    if record is not None:
                        record.tbegin = sock.record.tbegin - datetime.timedelta(
                            milliseconds=1
                        )
                        sock.record.group_id = group.id

            ret = await method(*args, **kwargs)

        return ret

    return hook


def set_hook_fastapi_routing_get_request_handler(
    records: HTTPRecords, method: Callable
):

    @wraps(method)
    def hook(*args, **kwargs):

        app = method(*args, **kwargs)

        app = decorate(records, app, set_hook_fastapi_app)

        return app

    return hook


@contextmanager
def hook_fastapi(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import fastapi.routing

        already_mapped: dict[Callable, Callable] = {}

        set_hook_fastapi_apirouter_add_api_route_with_already_mapped = (
            functools.partial(
                set_hook_fastapi_apirouter_add_api_route, already_mapped=already_mapped
            )
        )

        fastapi.routing.APIRouter.add_api_route = decorate(
            records,
            fastapi.routing.APIRouter.add_api_route,
            set_hook_fastapi_apirouter_add_api_route_with_already_mapped,
        )

        fastapi.routing.get_request_handler = decorate(
            records,
            fastapi.routing.get_request_handler,
            set_hook_fastapi_routing_get_request_handler,
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        fastapi.routing.APIRouter.add_api_route = undecorate(
            fastapi.routing.APIRouter.add_api_route
        )
        fastapi.routing.get_request_handler = undecorate(
            fastapi.routing.get_request_handler
        )
