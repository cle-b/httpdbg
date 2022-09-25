# -*- coding: utf-8 -*-
import io
import os
from urllib.parse import urlparse

from flask import abort, send_file
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
            "url": req.request.url,
            "method": req.request.method,
            "status_code": req.status_code,
            "reason": req.reason,
            "request": {
                "headers": req.list_headers(req.request.headers),
                "cookies": req.list_headers(req.request._cookies),
                "body": generate_preview(
                    f"/request/{req_id}/up",
                    "upload",
                    req.get_header(req.request.headers, "Content-Type"),
                    req.request.body,
                ),
            },
            "response": None,
            "exception": None,
            "initiator": req.initiator.to_json(),
        }

        if req.response is not None:

            details.update(
                {
                    "response": {
                        "headers": req.list_headers(req.response.headers),
                        "cookies": req.list_headers(req.response.cookies),
                        "body": generate_preview(
                            f"/request/{req_id}/down",
                            "download",
                            req.get_header(req.response.headers, "Content-Type"),
                            req.response.content,
                        ),
                    },
                }
            )

        if req.exception is not None:

            details.update(
                {
                    "exception": {
                        "type": str(type(req.exception)),
                        "message": str(req.exception),
                    },
                }
            )

        return details


class RequestContentDown(Resource):
    def get(self, req_id):
        req = get_request(req_id)

        filename = os.path.basename(urlparse(req.request.url).path)

        return send_file(
            io.BytesIO(req.response.content),
            download_name=filename,
            mimetype=req.get_header(req.response.headers, "Content-Type"),
        )


class RequestContentUp(Resource):
    def get(self, req_id):
        req = get_request(req_id)

        filename = os.path.basename(urlparse(req.request.url).path)

        return send_file(
            io.BytesIO(
                req.request.body
                if isinstance(req.request.body, bytes)
                else bytes(req.request.body.encode("utf-8"))
            ),
            download_name=f"upload-{filename}",
            mimetype="application/octet-stream",
        )


class RequestList(Resource):
    def get(self):
        global httpdebugk7

        k7 = {"id": httpdebugk7.id, "requests": {}}
        for id, req in httpdebugk7.requests.items():

            k7["requests"][id] = {
                "id": req.id,
                "unread": req.unread,
                "url": req.url,
                "netloc": req.netloc,
                "urlext": req.urlext,
                "status_code": req.status_code,
                "reason": req.reason,
                "verb": req.request.method,
                "initiator": req.initiator.to_json(full=False),
            }

        return k7
