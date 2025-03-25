# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_endpoint
from httpdbg.records import HTTPRecords


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


# we must not apply the hook more than once on a mapped endpoint function
already_mapped = {}


def set_hook_fastapi_add_api_route(records: HTTPRecords, method: Callable):

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

            args = [callargs[param] if x == original_view_func else x for x in args]
            if param in kwargs:
                kwargs[param] = callargs[param]

        return method(*args, **kwargs)

    return hook


@contextmanager
def hook_fastapi(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import fastapi
        import fastapi.routing

        fastapi.routing.APIRouter.add_api_route = decorate(
            records,
            fastapi.routing.APIRouter.add_api_route,
            set_hook_fastapi_add_api_route,
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        fastapi.routing.APIRouter.add_api_route = undecorate(
            fastapi.routing.APIRouter.add_api_route
        )
