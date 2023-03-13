# -*- coding: utf-8 -*-
import inspect

from httpdbg.utils import logger


def getcallargs(method, *args, **kwargs):
    while hasattr(
        method, "__httpdbg__"
    ):  # to retrieve the original method in case of nested hooks
        method = method.__httpdbg__
    callargs = inspect.signature(method).bind_partial(*args, **kwargs).arguments
    callargs.update(kwargs)
    logger.debug(f"{method} - {[arg for arg in callargs]}")
    return callargs


def decorate(records, method, hook):
    ori = method
    method = hook(records, method)
    method.__httpdbg__ = ori
    return method


def undecorate(method):
    return method.__httpdbg__
