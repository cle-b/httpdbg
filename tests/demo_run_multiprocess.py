import multiprocessing
import os
import requests


BASE_URL = os.environ.get(
    "HTTPDBG_TEST_MULTIPROCESS_BASE_URL", "http://localhost:4909/"
)


def make_request(depth=1, max_depth=3):

    requests.get(f"{BASE_URL}/get/{os.getpid()}")

    if depth < max_depth:
        ctx = multiprocessing.get_context("spawn")
        new_process = ctx.Process(target=make_request, args=(depth + 1, max_depth))
        new_process.start()
        new_process.join()


if __name__ == "__main__":
    print(
        "Made an HTTP request in the main process, a subprocess, and a nested subprocess."
    )
    make_request()
