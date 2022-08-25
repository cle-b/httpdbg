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
def test_preview_text_html():
    body = generate_preview(
        "path_to_htm",
        "filename.htm",
        "text/html",
        "<html><head><title>:-)</title></head><body>empty</body></html>",
    )
    preview = "<html>\n <head>\n  <title>\n   :-)\n  </title>\n </head>\n <body>\n  empty\n </body>\n</html>"

    assert body == {
        "filename": "filename.htm",
        "path": "path_to_htm",
        "text": preview,
    }


@pytest.mark.preview
def test_preview_text_html_wrong():
    body = generate_preview(
        "path_to_htm",
        "filename.htm",
        "text/html",
        None,
    )

    assert body == {
        "filename": "filename.htm",
        "path": "path_to_htm",
        "text": "error during html parsing",
    }


@pytest.mark.preview
def test_preview_application_json():
    body = generate_preview(
        "path_to_json",
        "filename.json",
        "application/json",
        '{"a": "1", "b": {"c": 2} }',
    )
    preview = '{\n    "a": "1",\n    "b": {\n        "c": 2\n    }\n}'

    assert body == {
        "filename": "filename.json",
        "path": "path_to_json",
        "text": preview,
    }


@pytest.mark.preview
def test_preview_application_json_wrong():
    body = generate_preview(
        "path_to_json",
        "filename.json",
        "application/json",
        "<html>:-D</html>",
    )

    assert body == {
        "filename": "filename.json",
        "path": "path_to_json",
        "text": "<html>:-D</html>",
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
