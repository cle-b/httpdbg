# -*- coding: utf-8 -*-
import json

from bs4 import BeautifulSoup


def generate_preview(path, filename, content_type, raw_data):

    body = {
        "path": path,
        "filename": filename,
    }

    if "text/html" in content_type.lower():
        try:
            soup = BeautifulSoup(raw_data, "html.parser")
            body["text"] = soup.prettify()
        except Exception:
            body["text"] = "error during html parsing"

    elif "application/json" in content_type.lower():
        try:
            body["text"] = json.dumps(json.loads(raw_data), sort_keys=True, indent=4)
        except Exception:
            body["text"] = raw_data

    elif "image/" in content_type.lower():
        body["image"] = True

    elif isinstance(raw_data, str):
        body["text"] = raw_data

    elif isinstance(raw_data, bytes):
        try:
            body["text"] = str(raw_data.decode("utf-8"))
        except Exception:
            pass

    return body
