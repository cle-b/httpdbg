# -*- coding: utf-8 -*-
from contextlib import contextmanager
import glob
from http.server import BaseHTTPRequestHandler
import json
import mimetypes
import os
import re
from urllib.parse import urlparse, parse_qs

from httpdbg import __version__
from httpdbg.log import logger
from httpdbg.webapp.api import RequestListPayload, RequestPayload


@contextmanager
def silently_catch_error():
    try:
        yield
    except Exception as ex:
        logger().info(f"HttpbgHTTPRequestHandler - silently_catch_error - {str(ex)}")


class HttpbgHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, records, *args, **kwargs):
        self.records = records
        super().__init__(*args, **kwargs)

    @silently_catch_error()
    def do_GET(self):
        url = urlparse(self.path)

        # we try different method to serve the URL until the good one is done
        for serve in [
            self.serve_static,
            self.serve_requests,
            self.serve_request,
            self.serve_request_content_up,
            self.serve_request_content_down,
            self.serve_not_found,
        ]:
            if serve(url):
                break

    def serve_static(self, url):
        base_path = os.path.dirname(os.path.realpath(__file__))

        if not (
            (url.path.lower() in ["/", "index.htm", "index.html"])
            or url.path.startswith("/static/")
        ):
            return False

        if url.path.lower() in ["/", "index.htm", "index.html"]:
            self.path = "/static/index.htm"

        # get real path
        self.path = self.path.split("-+-")[0]

        fullpath = os.path.realpath(os.path.join(base_path, self.path[1:]))

        if not fullpath.startswith(base_path):
            # if the file is not in the static directory, we don't serve it
            return self.serve_not_found()

        if not os.path.exists(fullpath):
            return self.serve_not_found()
        else:
            self.send_response(200)
            self.send_header(
                "content-type", mimetypes.types_map[os.path.splitext(fullpath)[1]]
            )
            if self.path == "/static/index.htm":
                self.send_header_no_cache()
            else:
                self.send_header_with_cache(604800)
            self.end_headers()

            with open(fullpath, "rb") as f:
                filecontent = f.read()

                if b"$**PRELOAD_ICONS**$" in filecontent:
                    icons = ""
                    for icon in glob.glob(
                        os.path.realpath(base_path) + "/static/icons/*.svg"
                    ):
                        icon_path = icon.replace(os.path.realpath(base_path) + "/", "")
                        icons += f"    <link rel='preload' href='{icon_path}-+-$**HTTPDBG_VERSION**$' as='image' type='image/svg+xml' />\n"

                    filecontent = filecontent.replace(
                        b"$**PRELOAD_ICONS**$", icons.encode("utf-8")
                    )

                filecontent = filecontent.replace(
                    b"$**HTTPDBG_VERSION**$", __version__.encode("utf-8")
                )

                self.wfile.write(filecontent)

        return True

    def serve_requests(self, url):
        if not (url.path.lower() == "/requests"):
            return False

        query = parse_qs(url.query)

        if query.get("id", [""])[0] == self.records.id:
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

    def serve_request(self, url):
        regexp = r"/request/([\w\-]+)"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found()

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

    def serve_request_content_up(self, url):
        regexp = r"/request/([\w\-]+)/up"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found()

        req = self.records.requests[req_id]

        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(
            req.request.content.encode("utf-8")
            if isinstance(req.request.content, str)
            else req.request.content
        )

        return True

    def serve_request_content_down(self, url):
        regexp = r"/request/([\w\-]+)/down"

        if re.fullmatch(regexp, url.path) is None:
            return False

        req_id = re.findall(regexp, url.path)[0]

        if req_id not in self.records.requests:
            return self.serve_not_found()

        req = self.records.requests[req_id]

        self.send_response(200)
        self.send_header("Content-type", req.response.get_header("Content-Type"))
        self.send_header_no_cache()
        self.end_headers()
        self.wfile.write(req.response.content)

        return True

    def serve_not_found(self, *kwargs):
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
