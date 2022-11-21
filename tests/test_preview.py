# -*- coding: utf-8 -*-
import pytest

from httpdbg.webapp.preview import generate_preview


@pytest.mark.preview
def test_preview_unknown_type_text():
    body = generate_preview("apath", "afilename", "unknown/type", "a text")
    assert body == {"filename": "afilename", "path": "apath", "text": "a text"}


@pytest.mark.preview
def test_preview_unknown_type_bytes():
    body = generate_preview("apath", "afilename", "unknown/type", b"a text")
    assert body == {"filename": "afilename", "path": "apath", "text": "a text"}


@pytest.mark.preview
@pytest.mark.parametrize(
    "content_type",
    ["text/html", "application/xhtml+xml", "application/xml", "text", ""],
)
def test_preview_xml(content_type):
    raw_data = "<html><head><title>:-)</title></head><body>empty</body></html>"
    body = generate_preview(
        "path_to_htm",
        "filename.htm",
        content_type,
        raw_data,
    )
    parsed = '<?xml version="1.0" ?>\n<html>\n   <head>\n      <title>:-)</title>\n   </head>\n   <body>empty</body>\n</html>'

    assert body == {
        "filename": "filename.htm",
        "path": "path_to_htm",
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
@pytest.mark.parametrize("content_type", ["text/json", "application/json", "text", ""])
def test_preview_json(content_type):
    raw_data = '{"a": "1", "b": {"c": 2} }'
    body = generate_preview(
        "path_to_json",
        "filename.json",
        "application/json",
        raw_data,
    )
    parsed = '{\n    "a": "1",\n    "b": {\n        "c": 2\n    }\n}'

    assert body == {
        "filename": "filename.json",
        "path": "path_to_json",
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
def test_preview_query_string():
    raw_data = "a=1&b=2&c=%7B%27er%27%3A+43434%7D"
    body = generate_preview(
        "path_to_json",
        "filename.json",
        "application/x-www-form-urlencoded",
        raw_data,
    )
    parsed = "a=1\n\nb=2\n\nc={'er': 43434}"

    assert body == {
        "filename": "filename.json",
        "path": "path_to_json",
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
def test_preview_query_string_not_urlencoded_mimetype():
    raw_data = "a=1&b=2&c=%7B%27er%27%3A+43434%7D"
    body = generate_preview(
        "path_to_json",
        "filename.json",
        "test/plain",
        raw_data,
    )

    assert body == {
        "filename": "filename.json",
        "path": "path_to_json",
        "text": raw_data,
    }


@pytest.mark.preview
def test_preview_image():
    body = generate_preview("path_to_img", "filename.png", "image/png", None)

    assert body == {
        "filename": "filename.png",
        "path": "path_to_img",
        "image": True,
    }


def test_preview_application_no_content_type_text():
    body = generate_preview(
        "path_to_text",
        "txt",
        "",
        "just text",
    )

    assert body == {
        "filename": "txt",
        "path": "path_to_text",
        "text": "just text",
    }


def test_preview_application_no_content_type_bytes():
    body = generate_preview(
        "path_to_bytes",
        "bytes",
        "",
        "just éà bytes".encode("utf-8"),
    )

    assert body == {
        "filename": "bytes",
        "path": "path_to_bytes",
        "text": "just éà bytes",
    }
