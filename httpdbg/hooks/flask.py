# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import functools
from functools import wraps
from typing import Generator


from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_endpoint
from httpdbg.records import HTTPRecords


def set_hook_flask_endpoint(records: HTTPRecords, method: Callable):

    @wraps(
        method
    )  # to avoid AssertionError: View function mapping is overwriting an existing endpoint function: hook
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


def set_hook_flask_add_url_rule(
    records: HTTPRecords,
    method: Callable,
    already_mapped: dict[Callable, Callable],
):

    def hook(*args, **kwargs):

        callargs = getcallargs(method, *args, **kwargs)

        param = "view_func"

        if param in callargs:
            original_view_func = callargs[param]
            if original_view_func not in already_mapped:
                callargs[param] = decorate(
                    records, callargs[param], set_hook_flask_endpoint
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


def set_hook_flask_register_error_handler(
    records: HTTPRecords,
    method: Callable,
    already_mapped: dict[Callable, Callable],
):

    def hook(*args, **kwargs):

        callargs = getcallargs(method, *args, **kwargs)

        param = "f"

        if param in callargs:
            original_view_func = callargs[param]
            if original_view_func not in already_mapped:
                callargs[param] = decorate(
                    records, callargs[param], set_hook_flask_endpoint
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


@contextmanager
def hook_flask(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import flask

        # we must not apply the hook more than once on a mapped endpoint function
        # AssertionError: View function mapping is overwriting an existing endpoint function: xxxx
        already_mapped: dict[Callable, Callable] = {}

        set_hook_flask_add_url_rule_with_already_mapped = functools.partial(
            set_hook_flask_add_url_rule, already_mapped=already_mapped
        )

        flask.Flask.add_url_rule = decorate(
            records,
            flask.Flask.add_url_rule,
            set_hook_flask_add_url_rule_with_already_mapped,
        )

        set_hook_flask_register_error_handler_with_already_mapped = functools.partial(
            set_hook_flask_register_error_handler, already_mapped=already_mapped
        )

        flask.Flask.register_error_handler = decorate(
            records,
            flask.Flask.register_error_handler,
            set_hook_flask_register_error_handler_with_already_mapped,
        )
        flask.Flask.handle_exception = decorate(
            records, flask.Flask.handle_exception, set_hook_flask_endpoint
        )
        flask.Flask.handle_http_exception = decorate(
            records, flask.Flask.handle_http_exception, set_hook_flask_endpoint
        )
        flask.Flask.handle_user_exception = decorate(
            records, flask.Flask.handle_user_exception, set_hook_flask_endpoint
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        flask.Flask.add_url_rule = undecorate(flask.Flask.add_url_rule)
        flask.Flask.register_error_handler = undecorate(
            flask.Flask.register_error_handler
        )
        flask.Flask.handle_exception = undecorate(flask.Flask.handle_exception)
        flask.Flask.handle_http_exception = undecorate(
            flask.Flask.handle_http_exception
        )
        flask.Flask.handle_user_exception = undecorate(
            flask.Flask.handle_user_exception
        )
