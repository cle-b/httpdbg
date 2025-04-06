# -*- coding: utf-8 -*-
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import Generator

from httpdbg.hooks.utils import decorate
from httpdbg.hooks.utils import getcallargs
from httpdbg.hooks.utils import undecorate
from httpdbg.records import HTTPRecords


def set_hook_starlette_request_init(records: HTTPRecords, method: Callable):

    @wraps(method)
    def hook(self, *args, **kwargs):

        callargs = getcallargs(method, self, *args, **kwargs)

        if "receive" in callargs:
            if hasattr(callargs["receive"], "__self__"):
                if hasattr(callargs["receive"].__self__, "transport"):
                    if hasattr(
                        callargs["receive"].__self__.transport,
                        "_TCPTransport__httpdbg_socketdata",
                    ):
                        # make the link between starlette.requests.Request (self) and uvicorn.protocols.http.httptools_impl.HttpToolsProtocol (socketdata)
                        self.__httpdbg_socketdata_id = callargs[
                            "receive"
                        ].__self__.transport._TCPTransport__httpdbg_socketdata.id

        return method(self, *args, **kwargs)

    return hook


@contextmanager
def hook_starlette(records: HTTPRecords) -> Generator[None, None, None]:
    hooks = False
    try:
        import starlette.requests

        starlette.requests.Request.__init__ = decorate(
            records,
            starlette.requests.Request.__init__,
            set_hook_starlette_request_init,
        )

        hooks = True
    except ImportError:
        pass

    yield

    if hooks:
        starlette.requests.Request.__init__ = undecorate(
            starlette.requests.Request.__init__
        )
