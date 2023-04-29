# -*- coding: utf-8 -*-
import json
import urllib
from typing import Tuple, Dict, Union
from xml.dom import minidom


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
    path: str, filename: str, raw_data: bytes, content_type: str, content_encoding: str
) -> Dict[str, Union[str, bool]]:
    body: Dict[str, Union[str, bool]] = {
        "path": path,
        "filename": filename,
    }

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

        if body.get("text"):
            if isinstance(body["text"], str):
                # json
                try:
                    body["parsed"] = json.dumps(
                        json.loads(body["text"]), sort_keys=True, indent=4
                    )
                except Exception:
                    # xml, ...
                    try:
                        lines = minidom.parseString(body["text"]).toprettyxml(
                            indent="   "
                        )
                        body["parsed"] = "\n".join(
                            [line for line in lines.split("\n") if line.strip() != ""]
                        )
                    except Exception:
                        # query string
                        try:
                            if (
                                parse_content_type(content_type)[0]
                                == "application/x-www-form-urlencoded"
                            ):
                                qs = []
                                for key, value in urllib.parse.parse_qsl(
                                    body["text"], strict_parsing=True
                                ):
                                    if value:
                                        qs.append(f"{key}={value}")
                                if qs:
                                    body["parsed"] = "\n\n".join(qs)
                        except Exception:
                            pass

    return body
