import atexit
import json
import os
import sys
import time
import threading
import uuid

from httpdbg import HTTPRecords
from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.hooks.all import httprecord
from httpdbg.hooks.record import HTTPRecord
from httpdbg.hooks.recordhttp1 import HTTP1Record
from httpdbg.hooks.recordhttp2 import HTTP2Record
from httpdbg.log import logger

HTTPDBG_INITIATORS = []  # type: ignore
HTTPDBG_RECORD_SERVER = False


def _safe_write_json_file(filename, content):
    with open(f"{filename}.tmp", "wb") as f:
        f.write(json.dumps(content).encode("utf-8"))

    os.replace(f"{filename}.tmp", filename)


class HttpdbgRecorder:
    """Records the HTTP requests in subprocesses and saves them to disk."""

    def __init__(self):
        self._running: bool = False
        self.fname: str = os.path.join(
            os.environ[HTTPDBG_MULTIPROCESS_DIR], str(uuid.uuid1())
        )
        self.serialized: list[str] = []

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
        # initiators
        for initiator in self.records.initiators.values():
            if initiator.id not in self.serialized:
                self.serialized.append(initiator.id)
                filename = f"{self.fname}.{initiator.id}.httpdbg-initiator"
                _safe_write_json_file(filename, initiator.to_json())

        # groups
        for group in self.records.groups.values():
            if group.id not in self.serialized:
                self.serialized.append(group.id)
                filename = f"{self.fname}.{group.id}.httpdbg-group"
                _safe_write_json_file(filename, group.to_json())

        # requests
        for request in self.records.requests.values():
            if isinstance(request, HTTPRecord):
                marker = f"{request.id}-{request.last_update.isoformat()}"
                if marker not in self.serialized:
                    self.serialized.append(marker)
                    if isinstance(request, HTTP1Record):
                        filename = f"{self.fname}.{marker}.httpdbg-http1record"
                        _safe_write_json_file(filename, request.to_json())
                    elif isinstance(request, HTTP2Record):
                        filename = f"{self.fname}.{marker}.httpdbg-http2record"
                        _safe_write_json_file(filename, request.to_json())

    def start(self):
        """Start recording."""
        self.context = httprecord(
            initiators=HTTPDBG_INITIATORS, server=HTTPDBG_RECORD_SERVER
        )
        self.records: HTTPRecords = self.context.__enter__()
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
