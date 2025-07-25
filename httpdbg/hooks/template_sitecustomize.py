import atexit
import os
import pickle
import sys
import time
import threading
from typing import Union
import uuid

from httpdbg import HTTPRecords
from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.hooks.all import httprecord
from httpdbg.log import logger

HTTPDBG_INITIATORS = []  # type: ignore
HTTPDBG_RECORD_SERVER = False


class HttpdbgRecorder:
    """Records the HTTP requests in subprocesses and saves them to disk."""

    def __init__(self):
        self._running: bool = False
        self.fname: str = os.path.join(
            os.environ[HTTPDBG_MULTIPROCESS_DIR], str(uuid.uuid1())
        )
        self.context = None
        self.records: Union[HTTPRecords, None] = None

    def _save_to_disk_loop(self):
        while self._running:
            try:
                self.save_to_disk()
            except RuntimeError as ex:
                if "dictionary changed size during iteration" in str(ex):
                    # This happens because some new requests are recorded (or existing ones updated) while
                    # trying to save the HTTPRecords object on the disk to share it with the main process.
                    # Here we can ignore that exception, because this is only a best effort attempt to refresh
                    # the web interface. A last save is done before to exit the process.
                    logger().info(
                        "MultiProcess - _save_to_disk_loop - RuntimeError - dictionary changed size during iteration"
                    )
                else:
                    raise
            time.sleep(1)

    def save_to_disk(self):
        if self.records and len(self.records.requests) > 0:
            with open(f"{self.fname}.httpdbgrecords.tmp", "wb") as f:
                pickle.dump(self.records, f)
            os.replace(
                f"{self.fname}.httpdbgrecords.tmp", f"{self.fname}.httpdbgrecords"
            )

    def start(self):
        """Start recording."""
        self.context = httprecord(
            initiators=HTTPDBG_INITIATORS, server=HTTPDBG_RECORD_SERVER
        )
        self.records = self.context.__enter__()
        self._running = True
        self._thread = threading.Thread(target=self._save_to_disk_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop recording."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.save_to_disk()
        if self.context:
            self.context.__exit__(None, None, None)


if HTTPDBG_MULTIPROCESS_DIR in os.environ:

    if not hasattr(sys, "_httpdbg_enabled"):
        sys._httpdbg_enabled = True  # type: ignore[attr-defined]

        # start recording when the process starts and stop it when process exists
        httprecorder = HttpdbgRecorder()
        httprecorder.start()

        atexit.register(httprecorder.stop)
