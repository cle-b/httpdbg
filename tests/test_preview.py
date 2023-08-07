# -*- coding: utf-8 -*-
import pytest

from httpdbg.preview import generate_preview


@pytest.mark.preview
def test_preview_unknown_type_text():
    body = generate_preview("a text", "unknown/type", "")
    assert body == {"text": "a text", "content_type": "unknown/type"}


@pytest.mark.preview
def test_preview_unknown_type_bytes():
    body = generate_preview(b"a text", "unknown/type", "")
    assert body == {"text": "a text", "content_type": "unknown/type"}


@pytest.mark.preview
@pytest.mark.parametrize("content_type", ["text/json", "application/json", "text", ""])
def test_preview_text(content_type):
    raw_data = '{"a": "1", "b": {"c": 2} }'
    body = generate_preview(raw_data, content_type, "")

    assert body == {
        "text": raw_data,
        "content_type": content_type,
    }


@pytest.mark.preview
def test_preview_image():
    body = generate_preview(None, "image/png", "")

    assert body == {
        "image": True,
        "content_type": "image/png",
    }


def test_preview_application_no_content_type_text():
    body = generate_preview("just text", "", "")

    assert body == {
        "text": "just text",
        "content_type": "",
    }


def test_preview_application_no_content_type_bytes():
    body = generate_preview("just éà bytes".encode("utf-8"), "", "")

    assert body == {
        "text": "just éà bytes",
        "content_type": "",
    }
