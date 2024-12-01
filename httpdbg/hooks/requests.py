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


def set_hook_for_requests(records: HTTPRecords, method: Callable):
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
def hook_requests(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import requests

        requests.get = decorate(records, requests.get, set_hook_for_requests)
        requests.post = decorate(records, requests.post, set_hook_for_requests)
        requests.patch = decorate(records, requests.patch, set_hook_for_requests)
        requests.put = decorate(records, requests.put, set_hook_for_requests)
        requests.delete = decorate(records, requests.delete, set_hook_for_requests)
        requests.head = decorate(records, requests.head, set_hook_for_requests)
        requests.options = decorate(records, requests.options, set_hook_for_requests)

        requests.request = decorate(records, requests.request, set_hook_for_requests)

        requests.Session.get = decorate(
            records, requests.Session.get, set_hook_for_requests
        )
        requests.Session.post = decorate(
            records, requests.Session.post, set_hook_for_requests
        )
        requests.Session.patch = decorate(
            records, requests.Session.patch, set_hook_for_requests
        )
        requests.Session.put = decorate(
            records, requests.Session.put, set_hook_for_requests
        )
        requests.Session.delete = decorate(
            records, requests.Session.delete, set_hook_for_requests
        )
        requests.Session.head = decorate(
            records, requests.Session.head, set_hook_for_requests
        )
        requests.Session.options = decorate(
            records, requests.Session.options, set_hook_for_requests
        )

        requests.Session.request = decorate(
            records, requests.Session.request, set_hook_for_requests
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        requests.get = undecorate(requests.get)
        requests.post = undecorate(requests.post)
        requests.patch = undecorate(requests.patch)
        requests.put = undecorate(requests.put)
        requests.delete = undecorate(requests.delete)
        requests.head = undecorate(requests.head)
        requests.options = undecorate(requests.options)

        requests.request = undecorate(requests.request)

        requests.Session.get = undecorate(requests.Session.get)
        requests.Session.post = undecorate(requests.Session.post)
        requests.Session.patch = undecorate(requests.Session.patch)
        requests.Session.put = undecorate(requests.Session.put)
        requests.Session.delete = undecorate(requests.Session.delete)
        requests.Session.head = undecorate(requests.Session.head)
        requests.Session.options = undecorate(requests.Session.options)

        requests.Session.request = undecorate(requests.Session.request)
