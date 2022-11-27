# -*- coding: utf-8 -*-
import http


def list_cookies_headers_request(headers, cookies):
    # important - do not use request._cookies as is because it contains all the cookies
    # of the session or redirection ; list only the cookies present in the raw header.
    lst = []
    for key, header in headers.items():
        if key.lower() == "cookie":
            for name, value in cookies.items():
                if f"{name}={value}" in header:
                    madeleine = {"name": name, "value": value}
                    lst.append(madeleine)
    return lst


def list_cookies_headers_response(headers, cookies):
    # important - do not use response.cookies as is because it contains all the cookies
    # of the session or redirection ; list only the cookies present in the raw header.
    lst = []
    for key, header in headers.items():
        if key.lower() in ("set-cookie", "cookie"):
            for cookie in cookies:
                if f"{cookie.name}={cookie.value}" in header:
                    madeleine = {"name": cookie.name, "value": cookie.value}
                    attributes = []
                    # https://docs.python.org/3/library/http.cookiejar.html#cookie-objects
                    if cookie.port_specified:
                        attributes.append({"name": "port", "attr": cookie.port})
                    if cookie.domain_specified:
                        attributes.append({"name": "domain", "attr": cookie.domain})
                    if cookie.path:
                        attributes.append({"name": "path", "attr": cookie.path})
                    if cookie.comment:
                        attributes.append({"name": "comment", "attr": cookie.comment})
                    if cookie.comment_url:
                        attributes.append(
                            {"name": "comment_url", "attr": cookie.comment_url}
                        )
                    if cookie.expires:
                        attributes.append(
                            {
                                "name": "expires",
                                "attr": http.cookiejar.time2netscape(cookie.expires),
                            }
                        )
                    if cookie.discard:
                        attributes.append({"name": "Discard"})
                    if cookie.secure:
                        attributes.append({"name": "Secure"})
                    if "httponly" in [k.lower() for k in cookie._rest.keys()]:
                        attributes.append({"name": "HttpOnly"})
                    if cookie._rest.get("SameSite"):
                        attributes.append(
                            {
                                "name": "SameSite",
                                "attr": cookie._rest.get("SameSite"),
                            }
                        )
                    if attributes:
                        madeleine["attributes"] = attributes
                    lst.append(madeleine)
    return lst
