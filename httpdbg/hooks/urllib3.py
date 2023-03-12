# -*- coding: utf-8 -*-
from contextlib import contextmanager

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import get_initiator
from httpdbg.records import HTTPRecord


def set_hook_for_urrlib3(records, method):
    def hook(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)
            url = callargs.get("url")

            if url:
                record = HTTPRecord()

                record.initiator = get_initiator(records._initiators)
                record.url = url
                record.exception = ex

                records.requests[record.id] = record
            raise

    return hook


@contextmanager
def hook_urllib3(records):
    hooks = False
    try:
        import urllib3

        urllib3.PoolManager.request = decorate(
            records, urllib3.PoolManager.request, set_hook_for_urrlib3
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        urllib3.PoolManager.request = undecorate(urllib3.PoolManager.request)
