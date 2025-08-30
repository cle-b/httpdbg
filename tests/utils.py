import datetime
import socket

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import requests


def get_request_details(current_httpdbg_port, req_number):
    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    req_id = reqs[list(reqs.keys())[req_number]]["id"]
    return requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/{req_id}")


def get_request_content_up(current_httpdbg_port, req_number):
    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    req_id = reqs[list(reqs.keys())[req_number]]["id"]
    return requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/{req_id}/up")


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
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
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


def get_free_tcp_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
