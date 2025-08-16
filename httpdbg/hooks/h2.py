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


def set_hook_for_h2_send_headers(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)
        print(callargs)
        initiator_and_group = None
        try:
            with httpdbg_initiator(
                records, traceback.extract_stack(), method, *args, **kwargs
            ) as initiator_and_group:
                ret = method(*args, **kwargs)
            return ret
        except Exception as ex:
            raise
            # callargs = getcallargs(method, *args, **kwargs)

            # if "url" in callargs:
            #     if initiator_and_group:
            #         initiator, group, is_new = initiator_and_group
            #         if is_new:
            #             records.add_new_record_exception(
            #                 initiator, group, str(callargs["url"]), ex
            #             )
            # raise

    return hook


def set_hook_for_h2_send_data(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        callargs = getcallargs(method, *args, **kwargs)
        print(callargs)
        initiator_and_group = None
        try:
            with httpdbg_initiator(
                records, traceback.extract_stack(), method, *args, **kwargs
            ) as initiator_and_group:
                ret = method(*args, **kwargs)
            return ret
        except Exception as ex:
            raise
            # callargs = getcallargs(method, *args, **kwargs)

            # if "url" in callargs:
            #     if initiator_and_group:
            #         initiator, group, is_new = initiator_and_group
            #         if is_new:
            #             records.add_new_record_exception(
            #                 initiator, group, str(callargs["url"]), ex
            #             )
            # raise

    return hook


def set_hook_for_h2_receive_data(records: HTTPRecords, method: Callable):
    def hook(*args, **kwargs):
        # callargs = getcallargs(method, *args, **kwargs)
        # print(callargs)
        initiator_and_group = None
        try:
            with httpdbg_initiator(
                records, traceback.extract_stack(), method, *args, **kwargs
            ) as initiator_and_group:
                ret = method(*args, **kwargs)
            for event in ret:
                print(type(event))
                print(event)
            return ret
        except Exception as ex:
            raise
            # callargs = getcallargs(method, *args, **kwargs)

            # if "url" in callargs:
            #     if initiator_and_group:
            #         initiator, group, is_new = initiator_and_group
            #         if is_new:
            #             records.add_new_record_exception(
            #                 initiator, group, str(callargs["url"]), ex
            #             )
            # raise

    return hook


@contextmanager
def hook_h2(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import h2.connection

        h2.connection.H2Connection.send_headers = decorate(records, h2.connection.H2Connection.send_headers, set_hook_for_h2_send_headers)  # type: ignore[arg-type]
        h2.connection.H2Connection.send_data = decorate(records, h2.connection.H2Connection.send_data, set_hook_for_h2_send_data)  # type: ignore[arg-type]
        h2.connection.H2Connection.receive_data = decorate(records, h2.connection.H2Connection.receive_data, set_hook_for_h2_receive_data)  # type: ignore[arg-type]

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        h2.connection.H2Connection.send_headers = undecorate(h2.connection.H2Connection.send_headers)  # type: ignore[arg-type]
        h2.connection.H2Connection.send_data = undecorate(h2.connection.H2Connection.send_data)  # type: ignore[arg-type]
        h2.connection.H2Connection.receive_data = undecorate(h2.connection.H2Connection.receive_data)  # type: ignore[arg-type]
