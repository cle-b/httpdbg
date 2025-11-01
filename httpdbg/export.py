import base64
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import httpdbg
from httpdbg import HTTPRecords
from httpdbg.webapp.api import RequestListPayload, RequestPayload


def generate_html(records: HTTPRecords, for_export: bool = True) -> str:

    current_dir = Path(__file__).resolve().parent

    with open(Path(current_dir) / "webapp/static/index.htm") as findexhtml:
        html = findexhtml.read()

    html = html.replace("$**HTTPDBG_VERSION**$", httpdbg.__version__)

    # favicon
    with open(current_dir / "webapp/static/favicon.ico", "rb") as ffavicon:
        b64_icon = base64.b64encode(ffavicon.read()).decode("utf-8")
        data_uri = f"data:image/x-icon;base64,{b64_icon}"
        html = html.replace(
            '<link rel="shortcut icon" href="static/favicon.ico">',
            f'<link rel="icon" type="image/x-icon" href="{data_uri}">',
        )

    # icons
    def svg_file_to_symbol(svg_path: Path, symbol_id: str) -> str:
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        root = ET.parse(svg_path).getroot()
        symbol = ET.Element(
            "symbol", {"id": symbol_id, "viewBox": root.attrib["viewBox"]}
        )
        for child in list(root):
            symbol.append(child)
        return ET.tostring(symbol, encoding="unicode")

    icons_inline = ""
    for icon_path in (current_dir / "webapp/static/icons").glob("*.svg"):
        icons_inline += "\n        " + svg_file_to_symbol(
            icon_path, icon_path.name[:-4]
        )
    icons_inline = f'<svg width="0" height="0" style="position:absolute;visibility:hidden" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{icons_inline}\n    </svg>'
    html = html.replace("$**PRELOAD_ICONS**$", icons_inline)

    # css
    stylesheet_pattern = (
        r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']'
    )
    for stylesheet in re.findall(stylesheet_pattern, html):
        with open(Path(current_dir) / "webapp" / stylesheet) as fcss:
            html = html.replace(
                f'<link rel="stylesheet" href="{stylesheet}">',
                f"<style>{fcss.read()}</style>",
            )

    # js
    javascript_pattern = r'<script\s+[^>]*src=["\']([^"\']+)["\']'
    for js in re.findall(javascript_pattern, html):
        with open(Path(current_dir) / "webapp" / js) as fjs:
            html = html.replace(
                f'<script src="{js}"></script>', f"<script>{fjs.read()}</script>"
            )

    # static export of the requests data
    if for_export:
        static_all_requests = json.dumps(
            records, cls=RequestListPayload, ensure_ascii=False
        )
        map_requests: dict[str, object] = dict()
        for record in records:
            map_requests[record.id] = json.loads(json.dumps(record, cls=RequestPayload))
        static_requests: str = json.dumps(map_requests, ensure_ascii=False)

        def safe_for_script_tag(s: str) -> str:
            return s.replace("</script>", "<\\/script>")

        html_export = f"""
    <script id="all-requests" type="application/json">
        {safe_for_script_tag(static_all_requests)}
    </script>

    <script id="requests-map" type="application/json">
        {safe_for_script_tag(static_requests)}
    </script>

    <script>
    global.static_all_requests = JSON.parse(
        document.getElementById('all-requests').textContent
    );
    global.static_requests = JSON.parse(
        document.getElementById('requests-map').textContent
    );
    global.connected = false;
    </script>
"""

        html = html.replace("$**EXPORT**$", html_export)
    else:
        html = html.replace("$**EXPORT**$", "")

    return html


def export_html(records: HTTPRecords, filename: Path):
    with open(filename, "w") as f:
        f.write(generate_html(records))
