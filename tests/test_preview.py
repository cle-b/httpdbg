# -*- coding: utf-8 -*-
import pytest

from httpdbg.preview import generate_preview


@pytest.mark.preview
def test_preview_unknown_type_text():
    body = generate_preview("a text", "unknown/type", "")
    assert body == {"text": "a text"}


@pytest.mark.preview
def test_preview_unknown_type_bytes():
    body = generate_preview(b"a text", "unknown/type", "")
    assert body == {"text": "a text"}


@pytest.mark.preview
@pytest.mark.parametrize(
    "content_type",
    ["text/html", "application/xhtml+xml", "application/xml", "text", ""],
)
def test_preview_xml(content_type):
    raw_data = "<html><head><title>:-)</title></head><body>empty</body></html>"
    body = generate_preview(raw_data, content_type, "")
    parsed = '<?xml version="1.0" ?>\n<html>\n   <head>\n      <title>:-)</title>\n   </head>\n   <body>empty</body>\n</html>'

    assert body == {
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
@pytest.mark.parametrize("content_type", ["text/json", "application/json", "text", ""])
def test_preview_json(content_type):
    raw_data = '{"a": "1", "b": {"c": 2} }'
    body = generate_preview(raw_data, "application/json", "")
    parsed = '{\n    "a": "1",\n    "b": {\n        "c": 2\n    }\n}'

    assert body == {
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
def test_preview_query_string():
    raw_data = "a=1&b=2&c=%7B%27er%27%3A+43434%7D"
    body = generate_preview(
        raw_data,
        "application/x-www-form-urlencoded",
        "",
    )
    parsed = "a=1\n\nb=2\n\nc={'er': 43434}"

    assert body == {
        "text": raw_data,
        "parsed": parsed,
    }


@pytest.mark.preview
def test_preview_query_string_not_urlencoded_mimetype():
    raw_data = "a=1&b=2&c=%7B%27er%27%3A+43434%7D"
    body = generate_preview(raw_data, "test/plain", "")

    assert body == {
        "text": raw_data,
    }


@pytest.mark.preview
def test_preview_image():
    body = generate_preview(None, "image/png", "")

    assert body == {
        "image": True,
    }


def test_preview_application_no_content_type_text():
    body = generate_preview("just text", "", "")

    assert body == {
        "text": "just text",
    }


def test_preview_application_no_content_type_bytes():
    body = generate_preview("just éà bytes".encode("utf-8"), "", "")

    assert body == {
        "text": "just éà bytes",
    }
