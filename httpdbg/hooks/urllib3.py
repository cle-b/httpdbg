# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
import traceback
from typing import Generator

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import httpdbg_initiator
from httpdbg.records import HTTPRecords


def set_hook_for_urllib3(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        initiator = None
        try:
            with httpdbg_initiator(
                records, traceback.extract_stack(), method, *args, **kwargs
            ) as initiator:
                ret = method(*args, **kwargs)
            return ret
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)

            if "url" in callargs:
                if initiator:
                    records.add_new_record_exception(
                        initiator, str(callargs["url"]), ex
                    )
            raise

    return hook


@contextmanager
def hook_urllib3(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import urllib3

        # v1
        if hasattr(urllib3, "PoolManager"):
            urllib3.PoolManager.request = decorate(
                records, urllib3.PoolManager.request, set_hook_for_urllib3
            )
        if hasattr(urllib3, "HTTPConnectionPool"):
            urllib3.HTTPConnectionPool.request = decorate(
                records, urllib3.HTTPConnectionPool.request, set_hook_for_urllib3
            )
        # v2
        if hasattr(urllib3, "request"):
            urllib3.request = decorate(records, urllib3.request, set_hook_for_urllib3)

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        # v1
        if hasattr(urllib3, "PoolManager"):
            urllib3.PoolManager.request = undecorate(urllib3.PoolManager.request)
        if hasattr(urllib3, "HTTPConnectionPool"):
            urllib3.HTTPConnectionPool.request = undecorate(
                urllib3.HTTPConnectionPool.request
            )
        # v2
        if hasattr(urllib3, "request"):
            urllib3.request = undecorate(urllib3.request)
