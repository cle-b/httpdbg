# -*- coding: utf-8 -*-
from http.cookies import SimpleCookie


def get_headers(headers):
    all_headers = []
    for (key, value) in headers.items():
        if type(value) is list:  # response
            for val in value:
                all_headers.append({"name": key, "value": val})
        else:  # request
            all_headers.append({"name": key, "value": value})
    return sorted(
        all_headers,
        key=lambda h: h["name"].lower(),
    )


def get_header(headers, name):
    # return the first value of the header (if many)
    value = ""
    for header in get_headers(headers):
        if header["name"].lower() == name.lower():
            value = header["value"]
            break
    return value


def list_cookies_request(headers):
    cookies = []
    for (key, value) in headers.items():
        if key.lower() == "cookie":
            for cookie in value.split(";"):
                cookies.append(
                    {
                        "name": cookie[: cookie.find("=")].strip(),
                        "value": cookie[cookie.find("=") + 1 :].strip(),
                    }
                )
    return sorted(cookies, key=lambda h: h["name"])


def list_cookies_response(headers):
    cookies = []
    for (key, values) in headers.items():
        if key.lower() == "set-cookie":
            for value in values:
                simple_cookies = SimpleCookie()
                simple_cookies.load(value)
                for key, value in simple_cookies.items():
                    cookies.append(
                        {
                            "name": key,
                            "value": value.value,
                            "attributes": [
                                {"name": n, "value": v} for (n, v) in value.items()
                            ],
                        }
                    )
    return sorted(cookies, key=lambda h: h["name"])
