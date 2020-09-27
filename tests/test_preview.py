# -*- coding: utf-8 -*-
import pytest

from httpdbg.webapp.preview import generate_preview


@pytest.mark.preview
def test_preview_unknown_type():
    body = generate_preview("apath", "afilename", "unknown/type", "the_data")
    assert body == {"filename": "afilename", "path": "apath"}


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
