# -*- coding: utf-8 -*-
import json
from http.server import BaseHTTPRequestHandler
import mimetypes
import os
import re
from urllib.parse import urlparse, parse_qs

from httpdbg.webapp.api import RequestListPayload, RequestPayload


class HttpbgHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, record, *args, **kwargs):
        self.records = record
        super().__init__(*args, **kwargs)

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
        if not (
            (url.path.lower() in ["/", "index.htm", "index.html"])
            or url.path.startswith("/static/")
        ):
            return False

        if url.path.lower() in ["/", "index.htm", "index.html"]:
            self.path = "/static/index.htm"

        fullpath = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), self.path[1:])
        )

        if not fullpath.startswith(os.path.dirname(os.path.realpath(__file__))):
            # if the file is not in the static directory, we don't serve it
            return self.serve_not_found()

        if not os.path.exists(fullpath):
            return self.serve_not_found()
        else:
            self.send_response(200)
            self.send_header(
                "content-type", mimetypes.types_map[os.path.splitext(fullpath)[1]]
            )
            self.send_header_no_cache()
            self.end_headers()
            with open(fullpath, "rb") as f:
                self.wfile.write(f.read())

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
