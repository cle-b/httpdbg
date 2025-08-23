# -*- coding: utf-8 -*-
from collections.abc import Callable
import inspect
import typing
from typing import Any

from httpdbg.log import logger

if typing.TYPE_CHECKING:
    from httpdbg.records import HTTPRecords


def getcallargs(original_method, *args, **kwargs):
    while hasattr(
        original_method, "__httpdbg__"
    ):  # to retrieve the original method in case of nested hooks
        original_method = original_method.__httpdbg__

    callargs: dict[str, Any] = dict()

    try:
        callargs = (
            inspect.signature(original_method).bind_partial(*args, **kwargs).arguments
        )
    except Exception as ex:
        logger().debug(f"getcallargs - exception {str(ex)}")
        # TypeError('too many positional arguments') may occur when using pytest (seems related to teardown_method)
        i = 0
        for arg in args:
            i += 1
            callargs[f"_positional_argument{i}"] = arg

    callargs.update(kwargs)
    logger().info(f"getcallargs {original_method} - {[arg for arg in callargs]}")
    return callargs


def decorate(records: "HTTPRecords", method: Callable, hook: Callable):
    ori = method
    method = hook(records, method)
    method.__httpdbg__ = ori  # type: ignore[attr-defined]
    return method


def undecorate(method: Callable):
    return method.__httpdbg__  # type: ignore[attr-defined]
