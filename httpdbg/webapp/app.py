from collections.abc import Callable
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
import re
from urllib.parse import ParseResult
from urllib.parse import parse_qs
from urllib.parse import urlparse

from httpdbg.log import logger
from httpdbg.webapp.api import RequestListPayload, RequestPayload
from httpdbg.records import HTTPRecords


@contextmanager
def silently_catch_error():
    try:
        yield
    except Exception as ex:
        logger().info(
            f"HttpbgHTTPRequestHandler - silently_catch_error - {str(ex)}",
            exc_info=True,
        )


class HttpbgHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(
        self: "HttpbgHTTPRequestHandler", records: HTTPRecords, *args, **kwargs
    ):
        self.records = records
        super().__init__(*args, **kwargs)

    @silently_catch_error()
    def do_GET(self):
        url = urlparse(self.path)

        # we try different method to serve the URL until the good one is done
        serve_funcs: list[Callable[[ParseResult], bool]] = [
            self.serve_static,
            self.serve_requests,
            self.serve_request,
            self.serve_request_content_up,
            self.serve_request_content_down,
            self.serve_not_found,
        ]

        for serve in serve_funcs:
            if serve(url):
                break

    def serve_static(self, url: ParseResult):

        if url.path.lower() in ["/", "index.htm", "index.html"]:
            from httpdbg.export import generate_html

            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.send_header_no_cache()
            self.end_headers()
            self.wfile.write(
                generate_html(self.records, for_export=False).encode("utf-8")
            )
            return True

        if url.path.lower() == "favicon.ico":
            self.send_response(200)
            self.send_header("content-type", "image/x-icon")
            self.send_header_no_cache()
            self.end_headers()

            current_dir = Path(__file__).resolve().parent

            with open(Path(current_dir) / "static/favicon.ico") as f:
                filecontent = f.read()
                self.wfile.write(filecontent.encode("utf-8"))

            return True

        return False

    def serve_requests(self, url: ParseResult):
        if not (url.path.lower() == "/requests"):
            return False

        query = parse_qs(url.query)

        if query.get("id", [""])[0] == self.records.session.id:
            self.records.requests_already_loaded = int(
                query.get("requests_already_loaded", [0])[0]
            )
        else:
            self.records.requests_already_loaded = 0

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(
            json.dumps(self.records, cls=RequestListPayload).encode("utf-8")
        )

        return True

    def serve_request(self, url: ParseResult):
        regexp = r"/request/([\w\-]+)"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found(url)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(
            json.dumps(self.records.requests[req_id], cls=RequestPayload).encode(
                "utf-8"
            )
        )

        return True

    def serve_request_content_up(self, url: ParseResult):
        regexp = r"/request/([\w\-]+)/up"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found(url)

        req = self.records.requests[req_id]

        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(req.request.content)

        return True

    def serve_request_content_down(self, url: ParseResult):
        regexp = r"/request/([\w\-]+)/down"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found(url)

        req = self.records.requests[req_id]

        self.send_response(200)
        self.send_header("Content-type", req.response.get_header("Content-Type"))
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(req.response.content)

        return True

    def serve_not_found(self, url: ParseResult):
        self.send_response(404)
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(b"404 Not found")

        return True

    def log_message(self, format, *args):
        pass

    def send_header_no_cache(self):
        self.send_header("Cache-Control", "max-age=0, no-cache, no-store, private")

    def send_header_with_cache(self, seconds):
        self.send_header("Cache-Control", f"max-age={seconds}")
