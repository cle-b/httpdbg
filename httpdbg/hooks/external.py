# -*- coding: utf-8 -*-
from contextlib import contextmanager
from typing import Generator
import glob
import os
import pickle
import tempfile
import time
import threading
from typing import Union

from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.log import logger
from httpdbg.records import HTTPRecords


@contextmanager
def watcher_external(
    records: HTTPRecords,
    initiators: Union[list[str], None] = None,
    server: bool = False,
) -> Generator[HTTPRecords, None, None]:
    if HTTPDBG_MULTIPROCESS_DIR not in os.environ:
        with tempfile.TemporaryDirectory(prefix="httpdbg_") as httpdbg_multiprocess_dir:

            logger().info(f"watcher_external {httpdbg_multiprocess_dir}")
            os.environ[HTTPDBG_MULTIPROCESS_DIR] = httpdbg_multiprocess_dir

            # we use a custom sitecustomize.py script to record the request in the subprocesses.
            # It doesn't work if the subprocess is created using the "fork" method
            # instead of the "spawn" method.
            template = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "template_sitecustomize.py",
            )
            sitecustomize = os.path.join(httpdbg_multiprocess_dir, "sitecustomize.py")

            with open(template) as f:
                template_content = f.read()

            if initiators:
                template_content = template_content.replace(
                    "HTTPDBG_INITIATORS = []", f"HTTPDBG_INITIATORS = {initiators}", 1
                )

            template_content = template_content.replace(
                "HTTPDBG_RECORD_SERVER = False", f"HTTPDBG_RECORD_SERVER = {server}", 1
            )

            with open(sitecustomize, "w") as f:
                f.write(template_content)

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
        for dump in glob.glob(os.path.join(self.directory, "*.httpdbgrecords")):
            with open(dump, "rb") as dumpfile:
                newrecords: HTTPRecords = pickle.load(dumpfile)
                self.records.requests.update(newrecords.requests)
                self.records.initiators.update(newrecords.initiators)
                self.records.groups.update(newrecords.groups)

    def run(self):
        while self._running:
            self.load_dump()
            time.sleep(self.delay)

    def shutdown(self):
        self._running = False
        self.join(timeout=5)
        self.load_dump()
