# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
import glob
import os
import pickle
import tempfile
import time
import threading

from httpdbg.env import HTTPDBG_SUBPROCESS_DIR
from httpdbg.records import HTTPRecords


@contextmanager
def watcher_external(records: HTTPRecords) -> Generator[HTTPRecords, None, None]:
    try:
        if HTTPDBG_SUBPROCESS_DIR not in os.environ:
            with tempfile.TemporaryDirectory(
                prefix="httpdbg"
            ) as httpdbg_subprocess_dir:
                os.environ[HTTPDBG_SUBPROCESS_DIR] = httpdbg_subprocess_dir

                watcher = WatcherSubprocessDirThread(records)
                watcher.start()

                yield records

                watcher.shutdown()
                watcher.join()
        else:
            yield records
    except Exception as ex:
        if watcher:
            watcher.shutdown()
        raise ex


class WatcherSubprocessDirThread(threading.Thread):
    def __init__(self, records: HTTPRecords, delay: int = 2) -> None:
        self.stop = False
        self.records = records
        self.delay = delay
        threading.Thread.__init__(self)

    def load_dump(self):
        for dump in glob.glob(f"{os.environ[HTTPDBG_SUBPROCESS_DIR]}/*.httpdbgrecords"):
            with open(dump, "rb") as dumpfile:
                newrecords = pickle.load(dumpfile)
                self.records.requests.update(newrecords.requests)

    def run(self):
        while not self.stop:
            time.sleep(self.delay)
            self.load_dump()

    def shutdown(self):
        self.stop = True
