import requests
import statistics
import time


def run_get(fnc, nb):
    times = []
    tb = time.time()
    for _ in range(nb):
        t0 = time.time()
        assert fnc("http://localhost:8000").content == b'"Hello, World!"'
        t1 = time.time()
        times.append(t1 - t0)
    te = time.time()
    print(
        f"{int(min(times)*1000)},{int(max(times)*1000)},{int(statistics.median(times)*1000)},{int((te-tb)*1000)}"
    )


if __name__ == "__main__":
    run_get(requests.get, 1000)
