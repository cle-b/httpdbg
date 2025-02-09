# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
import glob
import os
import pickle
import shutil
import tempfile
import time
import threading

from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.log import logger
from httpdbg.records import HTTPRecords


@contextmanager
def watcher_external(records: HTTPRecords) -> Generator[HTTPRecords, None, None]:
    remove_environment_variable = False

    if HTTPDBG_MULTIPROCESS_DIR not in os.environ:
        with tempfile.TemporaryDirectory(prefix="httpdbg") as httpdbg_multiprocess_dir:

            logger().info(f"watcher_external {httpdbg_multiprocess_dir}")
            remove_environment_variable = True
            os.environ[HTTPDBG_MULTIPROCESS_DIR] = httpdbg_multiprocess_dir

            # we use a custom sitecustomize.py script to record the request in the subprocesses.
            # It doesn't work if the subprocess is created using the "fork" method
            # instead of the "spawn" method.
            template = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "template_sitecustomize.py",
            )
            sitecustomize = os.path.join(httpdbg_multiprocess_dir, "sitecustomize.py")

            shutil.copy(template, sitecustomize)

            if "PYTHONPATH" in os.environ:
                os.environ["PYTHONPATH"] = (
                    f"{httpdbg_multiprocess_dir}:{os.environ['PYTHONPATH']}"
                )
            else:
                os.environ["PYTHONPATH"] = httpdbg_multiprocess_dir

            try:
                watcher = WatcherSubprocessDirThread(
                    records, httpdbg_multiprocess_dir, 1.0
                )
                watcher.start()

                yield records
            finally:
                watcher.shutdown()
                if remove_environment_variable and (
                    HTTPDBG_MULTIPROCESS_DIR in os.environ
                ):
                    del os.environ[HTTPDBG_MULTIPROCESS_DIR]
    else:
        yield records


class WatcherSubprocessDirThread(threading.Thread):
    def __init__(self, records: HTTPRecords, directory: str, delay: float) -> None:
        self.records: HTTPRecords = records
        self.directory: str = directory
        self.delay: float = delay
        self._running: bool = True
        threading.Thread.__init__(self)

    def load_dump(self):
        for dump in glob.glob(f"{self.directory}/*.httpdbgrecords"):
            with open(dump, "rb") as dumpfile:
                newrecords: HTTPRecords = pickle.load(dumpfile)
                self.records.requests.update(newrecords.requests)
                self.records.initiators.update(newrecords.initiators)
                self.records.groups.update(newrecords.groups)

    def run(self):
        while self._running and (HTTPDBG_MULTIPROCESS_DIR in os.environ):
            self.load_dump()
            time.sleep(self.delay)

    def shutdown(self):
        self._running = False
        self.join(timeout=5)
        self.load_dump()
