# -*- coding: utf-8 -*-
import inspect

from httpdbg.utils import logger


def getcallargs(original_method, *args, **kwargs):
    while hasattr(
        original_method, "__httpdbg__"
    ):  # to retrieve the original method in case of nested hooks
        original_method = original_method.__httpdbg__

    try:
        callargs = (
            inspect.signature(original_method).bind_partial(*args, **kwargs).arguments
        )
    except Exception as ex:
        logger.info(f"getcallargs - exception {str(ex)}")
        # TypeError('too many positional arguments') may occur when using pytest (seems related to teardown_method)
        callargs = {}
        i = 0
        for arg in args:
            i += 1
            callargs[f"_positional_argument{i}"] = arg

    callargs.update(kwargs)
    logger.info(f"getcallargs {original_method} - {[arg for arg in callargs]}")
    return callargs


def decorate(records, method, hook):
    ori = method
    method = hook(records, method)
    method.__httpdbg__ = ori
    return method


def undecorate(method):
    return method.__httpdbg__
