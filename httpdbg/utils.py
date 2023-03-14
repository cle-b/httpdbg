# -*- coding: utf-8 -*-
from http.cookies import SimpleCookie
import logging
import os
import secrets
import string

logger = logging.getLogger("httpdbg")
logger.setLevel(100)
log_level = os.environ.get("HTTPDBG_LOG")
if log_level is not None:
    logging.basicConfig(level=int(log_level), format="%(message)s")
    logger.setLevel(int(log_level))


def get_new_uuid():
    # important - the uuid must be compatible with method naming rules
    return "".join(secrets.choice(string.ascii_letters) for i in range(10))


def chunked_to_bytes(chunked):
    data = bytes()
    try:
        b1 = 0
        while b1 < len(chunked):
            sep = chunked[b1:].find(b"\r\n")
            size = int(chunked[b1 : b1 + sep], 16)
            data += chunked[b1 + sep + 2 : b1 + sep + 2 + size]
            b1 = b1 + sep + 2 + size + 2
        return data
    except Exception:
        # the chunked data can be incomplete or malformated
        return bytes()


def list_cookies_headers_request_simple_cookies(headers):
    lst = []
    for header in headers:
        if header["name"].lower() == "cookie":
            cookies = SimpleCookie()
            cookies.load(header["value"])
            for name, cookie in cookies.items():
                madeleine = {"name": name, "value": cookie.value}
                lst.append(madeleine)
    return lst


def list_cookies_headers_response_simple_cookies(headers):
    lst = []
    for header in headers:
        if header["name"].lower() == "set-cookie":
            cookies = SimpleCookie()
            cookies.load(header["value"])
            for name, cookie in cookies.items():
                madeleine = {"name": name, "value": cookie.value}
                attributes = []
                # https://docs.python.org/3/library/http.cookies.html
                if cookie.get("expires"):
                    attributes.append(
                        {"name": "expires", "attr": cookie.get("expires")}
                    )
                if cookie.get("path"):
                    attributes.append({"name": "path", "attr": cookie.get("path")})
                if cookie.get("comment"):
                    attributes.append(
                        {"name": "comment", "attr": cookie.get("comment")}
                    )
                if cookie.get("domain"):
                    attributes.append({"name": "domain", "attr": cookie.get("domain")})
                if cookie.get("max-age"):
                    attributes.append(
                        {"name": "max-age", "attr": cookie.get("max-age")}
                    )
                if cookie.get("samesite"):
                    attributes.append(
                        {"name": "SameSite", "attr": cookie.get("samesite")}
                    )
                if cookie.get("secure"):
                    attributes.append({"name": "Secure"})
                if cookie.get("httponly"):
                    attributes.append({"name": "HttpOnly"})
                if attributes:
                    madeleine["attributes"] = attributes
                lst.append(madeleine)
    return lst
