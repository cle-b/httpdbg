from collections.abc import Generator
from contextlib import contextmanager
import json
import glob
import os
import tempfile
import time
import threading

from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.hooks.recordhttp1 import HTTP1Record
from httpdbg.hooks.recordhttp2 import HTTP2Record
from httpdbg.initiator import Group
from httpdbg.initiator import Initiator
from httpdbg.log import logger
from httpdbg.records import HTTPRecords


def _safe_delete_file(filename):
    try:
        os.remove(filename)
    except Exception as ex:
        logger().info(
            f"_safe_delete_file - silently_catch_error - {str(ex)}",
            exc_info=True,
        )


@contextmanager
def watcher_external(
    records: HTTPRecords,
    initiators: list[str] | None = None,
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
        # initiators
        for filename in glob.glob(os.path.join(self.directory, "*.httpdbg-initiator")):
            with open(filename, "r") as f:
                data = json.load(f)
                initiator = Initiator.from_json(data)
                self.records.initiators[initiator.id] = initiator
            _safe_delete_file(filename)

        # group
        for filename in glob.glob(os.path.join(self.directory, "*.httpdbg-group")):
            with open(filename, "r") as f:
                data = json.load(f)
                group = Group.from_json(data)
                self.records.groups[group.id] = group
            _safe_delete_file(filename)

        # httprecord HTTP1
        for filename in sorted(
            glob.glob(os.path.join(self.directory, "*.httpdbg-http1record"))
        ):
            with open(filename, "r") as f:
                data = json.load(f)
                http1record = HTTP1Record.from_json(data)
                self.records.requests[http1record.id] = http1record
            _safe_delete_file(filename)

        # httprecord HTTP2
        for filename in sorted(
            glob.glob(os.path.join(self.directory, "*.httpdbg-http2record"))
        ):
            with open(filename, "r") as f:
                data = json.load(f)
                http2record = HTTP2Record.from_json(data)
                self.records.requests[http2record.id] = http2record
            _safe_delete_file(filename)

    def run(self):
        while self._running:
            self.load_dump()
            time.sleep(self.delay)

    def shutdown(self):
        self._running = False
        self.join(timeout=5)
        self.load_dump()
