import asyncio
import contextlib
import datetime
import ipaddress
from pathlib import Path
import ssl
import tempfile
import time
import threading

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import httpbin
from hypercorn.config import Config
from hypercorn.asyncio import serve


def generate_self_signed_cert(certfile="cert.pem", keyfile="key.pem"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "XX"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "TestState"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "TestLocality"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TestOrg"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    san = x509.SubjectAlternativeName(
        [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        )
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
        )
        .add_extension(san, critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(keyfile, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(certfile, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


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
    Run httpbin under Hypercorn with HTTP/2 + self-signed TLS in a background thread.
    Yields the base URL.
    """
    app = httpbin.app  # WSGI

    with tempfile.TemporaryDirectory() as tmpdir:
        cert_path = Path(tmpdir) / "cert-httpdbg-http2-test-only.pem"
        key_path = Path(tmpdir) / "key-httpdbg-http2-test-only.pem"
        generate_self_signed_cert(cert_path, key_path)

        cfg = Config()
        cfg.bind = [f"{host}:{port}"]
        cfg.alpn_protocols = ["h2", "http/1.1"]
        cfg.certfile = str(cert_path)
        cfg.keyfile = str(key_path)
        cfg.loglevel = "warning"

        cfg.keep_alive_timeout = 5
        cfg.shutdown_timeout = 5
        cfg.graceful_timeout = 5

        stop_flag = threading.Event()

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _install_sslnoise_filter(loop)

            async def _shutdown_trigger():
                while not stop_flag.is_set():
                    await asyncio.sleep(0.5)

            try:
                loop.run_until_complete(
                    serve(app, cfg, shutdown_trigger=_shutdown_trigger)
                )
            finally:
                loop.stop()
                loop.close()

        thread = threading.Thread(
            target=_run, name="hypercorn-http2-httpbin", daemon=True
        )
        thread.start()

        time.sleep(5)

        try:
            yield f"https://{host}:{port}"
        finally:
            time.sleep(1)
            stop_flag.set()
            thread.join(timeout=10)


if __name__ == "__main__":
    with http2_httpbin_server("localhost", 8998) as url:
        print(f"httpbin (http/2) available at {url}")
        input("Press enter to quit")
