# -*- coding: utf-8 -*-
import json
import urllib
from xml.dom import minidom


def parse_content_type(content_type):
    s = content_type.split(";")
    media_type = s[0]
    directives = {}
    for directive in s[1:]:
        sp = directive.split("=")
        if len(sp) == 2:
            directives[sp[0].strip()] = sp[1].strip()
    return media_type, directives


def generate_preview(path, filename, content_type, raw_data):

    body = {
        "path": path,
        "filename": filename,
    }

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
            # json
            try:
                body["parsed"] = json.dumps(
                    json.loads(body["text"]), sort_keys=True, indent=4
                )
            except Exception:
                # xml, ...
                try:
                    lines = minidom.parseString(body["text"]).toprettyxml(indent="   ")
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
