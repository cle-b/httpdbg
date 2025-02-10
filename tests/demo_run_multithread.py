import os
import requests
import threading

BASE_URL = os.environ.get("HTTPDBG_TEST_MULTITHREAD_BASE_URL", "http://localhost:4909/")


def make_request(depth=1, max_depth=3):

    requests.get(f"{BASE_URL}/get/{os.getpid()}")

    if depth < max_depth:
        new_thread = threading.Thread(target=make_request, args=(depth + 1, max_depth))
        new_thread.start()
        new_thread.join()


if __name__ == "__main__":
    print(
        "Made an HTTP request in the main thread, a child thread, and a nested child thread."
    )

    make_request()
