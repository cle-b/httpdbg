# -*- coding: utf-8 -*-
import io
import os
from urllib.parse import urlparse
import uuid

from flask import abort, send_file
from flask_restful import Resource

from .informations import http_verbs
from ..vcrpy import get_header, get_headers, list_cookies_request, list_cookies_response
from .preview import generate_preview


httpdebugk7 = {
    "k7": None,
    "id": str(uuid.uuid4()),
    "requests": {"available": [], "getted": []},
}  # this global variable is used to share the cassettes (requests's informations recorded)


class Request(Resource):
    def get(self, req_id):
        global httpdebugk7

        if httpdebugk7["k7"] is None:
            abort(404)

        if int(req_id) > len(httpdebugk7["k7"].requests):
            abort(404)

        if req_id not in httpdebugk7["requests"]["getted"]:
            httpdebugk7["requests"]["getted"].append(int(req_id))

        request = httpdebugk7["k7"].requests[int(req_id)]

        details = {
            "url": request.uri,
            "method": request.method,
            "protocol": request.protocol,
            "status": None,
            "request": {
                "headers": get_headers(request.headers),
                "cookies": list_cookies_request(request.headers),
            },
            "response": None,
        }

        if request.body:
            details["request"]["body"] = generate_preview(
                f"/request/{req_id}/up",
                "upload",
                get_header(request.headers, "Content-Type"),
                request.body,
            )

        if int(req_id) < len(httpdebugk7["k7"].responses):

            response = httpdebugk7["k7"].responses[int(req_id)]

            details.update(
                {
                    "status": response.get("status", {"code": "-", "message": "-"}),
                    "response": {
                        "headers": get_headers(response["headers"]),
                        "cookies": list_cookies_response(response["headers"]),
                    },
                }
            )

            if response["body"]["string"]:
                filename = os.path.basename(urlparse(request.uri).path)
                details["response"]["body"] = generate_preview(
                    f"/request/{req_id}/down",
                    filename,
                    get_header(response["headers"], "Content-Type"),
                    response["body"]["string"],
                )

        return details


class RequestContentDown(Resource):
    def get(self, req_id):
        global httpdebugk7

        if httpdebugk7["k7"] is None:
            abort(404)

        if int(req_id) > len(httpdebugk7["k7"].responses):
            abort(404)

        request = httpdebugk7["k7"].requests[int(req_id)]
        response = httpdebugk7["k7"].responses[int(req_id)]

        filename = os.path.basename(urlparse(request.uri).path)

        return send_file(
            io.BytesIO(response["body"]["string"]),
            download_name=filename,
            mimetype=get_header(response["headers"], "Content-Type"),
        )


class RequestContentUp(Resource):
    def get(self, req_id):
        global httpdebugk7

        if httpdebugk7["k7"] is None:
            abort(404)

        if int(req_id) > len(httpdebugk7["k7"].requests):
            abort(404)

        request = httpdebugk7["k7"].requests[int(req_id)]

        return send_file(
            io.BytesIO(request.body),
            download_name="upload",
            mimetype="application/octet-stream",
        )


class RequestList(Resource):
    def get(self):
        global httpdebugk7

        k7 = {"id": httpdebugk7["id"], "requests": []}
        for i in range(len(httpdebugk7["k7"].requests)):

            # we keep a list of all available requests to check if all of them have been getted
            if i not in httpdebugk7["requests"]["available"]:
                httpdebugk7["requests"]["available"].append(i)

            # for each request, we prepare a summary
            request = httpdebugk7["k7"].requests[i]
            response = httpdebugk7["k7"].responses[i]

            k7["requests"].append(
                {
                    "id": i,
                    "url": request.uri,
                    "status": response.get("status", {"code": 0, "message": "--"}),
                    "method": {
                        "verb": request.method,
                        "description": http_verbs.get(request.method.upper(), ""),
                    },
                    "src": request.src.to_json() if hasattr(request, "src") else None,
                }
            )

        return k7
