# -*- coding: utf-8 -*-
from contextlib import contextmanager
import json
import os
import tempfile
import time
import threading
from typing import Generator

from httpdbg.env import HTTPDBG_MULTIPROCESS_DIR
from httpdbg.initiator import Group
from httpdbg.initiator import Initiator
from httpdbg.log import logger
from httpdbg.records import HTTPRecord
from httpdbg.records import HTTPRecords


@contextmanager
def watcher_go(
    records: HTTPRecords,
) -> Generator[HTTPRecords, None, None]:
    if HTTPDBG_MULTIPROCESS_DIR not in os.environ:
        with tempfile.TemporaryDirectory(prefix="httpdbg_") as httpdbg_multiprocess_dir:

            logger().info(f"watcher_go {httpdbg_multiprocess_dir}")
            os.environ[HTTPDBG_MULTIPROCESS_DIR] = httpdbg_multiprocess_dir

            try:
                watcher = WatcherGoDirThread(records, httpdbg_multiprocess_dir, 1.0)
                watcher.start()

                yield records
            finally:
                watcher.shutdown()
    else:
        yield records


class WatcherGoDirThread(threading.Thread):
    def __init__(self, records: HTTPRecords, directory: str, delay: float) -> None:
        self.records: HTTPRecords = records
        self.directory: str = directory
        self.delay: float = delay
        self._running: bool = True
        threading.Thread.__init__(self)

    def get_go_traces(self):
        traces_filename = os.path.join(self.directory, "httpdbg-go-traces.json")
        if os.path.exists(traces_filename):
            with open(traces_filename, "r") as f:
                traces = json.load(f)
                for trace in traces:
                    if trace["trace_id"] not in self.records.requests.keys():
                        label = trace["initiator"]["code"]
                        full_label = f'File "{trace["initiator"]["filename"]}", line {trace["initiator"]["lineno"]}, in {trace["initiator"]["func_name"]}'
                        full_label += f"\n    {trace['initiator']['code']}"
                        stack = []
                        for line in trace["initiator"]["stack"]:
                            stack.append(f"{line['location']}, in {line['func_name']}")
                            code = line["code"].replace("\t", "    ")
                            stack.append(f"    {code}\n")

                        initiator = Initiator(label, full_label, stack)
                        self.records.add_initiator(initiator)
                        group = Group(label, full_label, False)
                        self.records.add_group(group)
                        record = HTTPRecord(
                            initiator.id,
                            group.id,
                        )
                        record.id = trace["trace_id"]
                        with open(trace["request_file"], "rb") as reqf:
                            record.send_data(reqf.read())
                        with open(trace["response_file"], "rb") as resf:
                            record.receive_data(resf.read())
                        self.records.requests[record.id] = record

    def run(self):
        while self._running:
            self.get_go_traces()
            time.sleep(self.delay)

    def shutdown(self):
        self._running = False
        self.join(timeout=5)
        self.get_go_traces()
