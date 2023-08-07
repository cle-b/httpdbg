# -*- coding: utf-8 -*-
from typing import Tuple, Dict, Union


def parse_content_type(content_type: str) -> Tuple[str, Dict[str, str]]:
    s = content_type.split(";")
    media_type = s[0]
    directives = {}
    for directive in s[1:]:
        sp = directive.split("=")
        if len(sp) == 2:
            directives[sp[0].strip()] = sp[1].strip()
    return media_type, directives


def generate_preview(
    raw_data: bytes, content_type: str, content_encoding: str
) -> Dict[str, Union[str, bool]]:
    body: Dict[str, Union[str, bool]] = {}

    body["content_type"] = content_type

    if content_encoding.lower() == "br":
        try:
            import brotli  # type: ignore

            raw_data = brotli.decompress(raw_data)
        except Exception:
            # if there is no brotli library available to decompress the data we keep the compressed data
            pass
    elif content_encoding.lower() == "gzip":
        try:
            import zlib

            raw_data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(raw_data)
        except Exception:
            pass
        # TODO deflate

    if "image/" in content_type.lower():
        body["image"] = True
    else:
        if isinstance(raw_data, str):
            body["text"] = raw_data
        elif isinstance(raw_data, bytes):
            try:
                body["text"] = raw_data.decode(
                    parse_content_type(content_type)[1].get("charset", "utf-8")
                )
            except Exception:
                pass

    return body
