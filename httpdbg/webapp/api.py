# -*- coding: utf-8 -*-
import io
import os
from urllib.parse import urlparse

from flask import abort, send_file, request
from flask_restful import Resource

from httpdbg.webapp.preview import generate_preview

from httpdbg.hook import HTTPRecords

httpdebugk7 = HTTPRecords()


def get_request(id):
    global httpdebugk7

    if id not in httpdebugk7.requests:
        abort(404)

    return httpdebugk7.requests[id]


class Request(Resource):
    def get(self, req_id):

        req = get_request(req_id)

        details = {
            "url": req.url,
            "method": req.method,
            "status_code": req.status_code,
            "reason": req.reason,
            "request": {
                "headers": req.request.headers,
                "cookies": req.request.cookies,
            },
            "response": None,
            "exception": None,
            "initiator": req.initiator.to_json(),
        }

        if req.request.content:
            details["request"]["body"] = generate_preview(
                f"/request/{req_id}/up",
                "upload",
                req.request.get_header("Content-Type"),
                req.request.content,
            )

        if req.response is not None:

            details["response"] = {
                "headers": req.response.headers,
                "cookies": req.response.cookies,
                "stream": req.stream,
            }

            if not req.stream:
                # TODO: we can't retrieve the content of the response if the stream mode has been used
                details["response"]["body"] = generate_preview(
                    f"/request/{req_id}/down",
                    "download",
                    req.response.get_header("Content-Type"),
                    req.response.content,
                )

        if req.exception is not None:

            details["exception"] = {
                "type": str(type(req.exception)),
                "message": str(req.exception),
            }

        return details


class RequestContentDown(Resource):
    def get(self, req_id):
        req = get_request(req_id)

        filename = os.path.basename(urlparse(req.url).path)

        return send_file(
            io.BytesIO(req.response.content),
            download_name=filename,
            mimetype=req.response.get_header("Content-Type"),
        )


class RequestContentUp(Resource):
    def get(self, req_id):
        req = get_request(req_id)

        filename = os.path.basename(urlparse(req.url).path)

        return send_file(
            io.BytesIO(
                req.request.content
                if isinstance(req.request.content, bytes)
                else bytes(req.request.content.encode("utf-8"))
            ),
            download_name=f"upload-{filename}",
            mimetype="application/octet-stream",
        )


class RequestList(Resource):
    def get(self):
        global httpdebugk7

        if request.args.get("id") == httpdebugk7.id:
            httpdebugk7.requests_already_loaded = int(
                request.args.get("requests_already_loaded", 0)
            )
        else:
            httpdebugk7.requests_already_loaded = 0

        k7 = {"id": httpdebugk7.id, "requests": {}}
        for id, req in httpdebugk7.requests.items():

            k7["requests"][id] = {
                "id": req.id,
                "url": req.url,
                "netloc": req.netloc,
                "urlext": req.urlext,
                "status_code": req.status_code,
                "reason": req.reason,
                "verb": req.method,
                "initiator": req.initiator.to_json(full=False),
            }

        return k7
