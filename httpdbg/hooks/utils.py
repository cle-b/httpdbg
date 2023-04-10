# -*- coding: utf-8 -*-
import inspect

from httpdbg.utils import logger


def getcallargs(original_method, *args, **kwargs):
    while hasattr(
        original_method, "__httpdbg__"
    ):  # to retrieve the original method in case of nested hooks
        original_method = original_method.__httpdbg__
    callargs = (
        inspect.signature(original_method).bind_partial(*args, **kwargs).arguments
    )
    callargs.update(kwargs)
    logger.debug(f"{original_method} - {[arg for arg in callargs]}")
    return callargs


def decorate(records, method, hook):
    ori = method
    method = hook(records, method)
    method.__httpdbg__ = ori
    return method


def undecorate(method):
    return method.__httpdbg__
