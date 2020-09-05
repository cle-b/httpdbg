# -*- coding: utf-8 -*-
from itertools import count
import queue
import threading

from httpdbg import httpdbg


httpdbg_port = count(4500)


def _run_under_httpdbg(func, *args):
    current_httpdbg_port = next(httpdbg_port)
    excq = queue.Queue()

    evt_httpdbg = threading.Event()
    evt_main = threading.Event()

    def __test(evt_httpdbg, evt_main, current_httpdbg_port, excq, *args):
        with httpdbg(current_httpdbg_port):
            try:
                func(*args)
                evt_main.set()
                evt_httpdbg.wait()
            except Exception as e:
                excq.put(e)
                evt_main.set()
                evt_httpdbg.set()

    threading.Thread(
        name="testapi",
        target=__test,
        args=(evt_httpdbg, evt_main, current_httpdbg_port, excq, *args),
    ).start()

    evt_main.wait()

    if excq.qsize() != 0:
        raise excq.get()

    return evt_httpdbg.set, current_httpdbg_port
