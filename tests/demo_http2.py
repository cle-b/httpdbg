import asyncio
import contextlib
import tempfile
import threading
import time
import ssl

import httpbin
from hypercorn.config import Config
from hypercorn.asyncio import serve

from tests.utils import generate_self_signed_cert


def _install_sslnoise_filter(loop: asyncio.AbstractEventLoop):

    def handler(_loop, context):
        exc = context.get("exception")
        if isinstance(
            exc, ssl.SSLError
        ) and "APPLICATION_DATA_AFTER_CLOSE_NOTIFY" in str(exc):
            # we can ignore it as this server is only for test
            return
        _loop.default_exception_handler(context)

    loop.set_exception_handler(handler)


@contextlib.contextmanager
def http2_httpbin_server(host: str, port: int):
    """
    Run httpbin under Hypercorn with HTTP/2 + self-signed TLS,
    in a background thread. Yields the base URL.
    """
    app = httpbin.app

    with tempfile.TemporaryDirectory() as tmpdir:

        cert_path = f"{tmpdir}/cert-httpdbg-http2-test-only.pem"
        key_path = f"{tmpdir}/key-httpdbg-http2-test-only.pem"
        generate_self_signed_cert(cert_path, key_path)

        cfg = Config()
        cfg.bind = [f"{host}:{port}"]
        cfg.alpn_protocols = ["h2", "http/1.1"]
        cfg.certfile = str(cert_path)
        cfg.keyfile = str(key_path)
        cfg.loglevel = "warning"

        shutdown_event = asyncio.Event()

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _install_sslnoise_filter(loop)
            try:
                loop.run_until_complete(
                    serve(app, cfg, shutdown_trigger=shutdown_event.wait)
                )
            finally:
                loop.stop()
                loop.close()

        thread = threading.Thread(
            target=_run, name="hypercorn-http2-httpbin", daemon=True
        )
        thread.start()
        time.sleep(2)

        try:
            yield f"https://{host}:{port}"
        finally:
            shutdown_event.set()
            thread.join(timeout=5)


if __name__ == "__main__":
    with http2_httpbin_server("localhost", 8998) as url:
        print(f"httpbin (http/2) available at {url}")
        input("Press enter to quit")
