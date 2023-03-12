# -*- coding: utf-8 -*-
from contextlib import contextmanager

from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import undecorate
from httpdbg.initiator import get_initiator
from httpdbg.records import HTTPRecord


def set_hook_for_requests(records, method):
    def hook(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as ex:
            callargs = getcallargs(method, *args, **kwargs)
            request = callargs.get("request")

            if request:
                if hasattr(request, "url"):
                    record = HTTPRecord()

                    record.initiator = get_initiator(records._initiators)
                    record.url = str(request.url)
                    record.exception = ex

                    records.requests[record.id] = record
            raise

    return hook


@contextmanager
def hook_requests(records):
    hooks = False
    try:
        import requests

        requests.adapters.HTTPAdapter.send = decorate(
            records, requests.adapters.HTTPAdapter.send, set_hook_for_requests
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        requests.adapters.HTTPAdapter.send = undecorate(
            requests.adapters.HTTPAdapter.send
        )
