# -*- coding: utf-8 -*-
from json import JSONEncoder

from httpdbg.records import HTTPRecords
from httpdbg.records import HTTPRecord
from httpdbg.webapp.preview import generate_preview


class RequestPayload(JSONEncoder):
    def default(self, req: HTTPRecord) -> dict:
        payload = {
            "id": req.id,
            "url": req.url,
            "netloc": req.netloc,
            "urlext": req.urlext,
            "method": req.method,
            "status_code": req.status_code,
            "reason": req.reason,
            "request": None,
            "response": None,
            "exception": None,
            "initiator": req.initiator.to_json(),
            "in_progress": req.in_progress,
        }

        payload["request"] = {
            "headers": [header.to_json() for header in req.request.headers],
            "cookies": [cookie.to_json() for cookie in req.request.cookies],
        }

        if req.request.content:
            payload["request"]["body"] = generate_preview(  # type: ignore
                f"/request/{req.id}/up",
                "upload",
                req.request.content,
                req.request.get_header("Content-Type"),
                req.request.get_header("Content-Encoding"),
            )

        payload["response"] = {
            "headers": [header.to_json() for header in req.response.headers],
            "cookies": [cookie.to_json() for cookie in req.response.cookies],
        }

        if req.response.content:
            payload["response"]["body"] = generate_preview(  # type: ignore
                f"/request/{req.id}/down",
                "download",
                req.response.content,
                req.response.get_header("Content-Type"),
                req.response.get_header("Content-Encoding"),
            )

        if req.exception is not None:
            payload["exception"] = {
                "type": str(type(req.exception)),
                "message": str(req.exception),
            }

        return payload


class RequestListPayload(JSONEncoder):
    def default(self, records):
        assert isinstance(
            records, HTTPRecords
        ), "This encoder works only for HTTPRecords object."

        payload = {"id": records.id, "requests": {}}

        for id, req in records.requests.items():
            payload["requests"][id] = {
                "id": req.id,
                "url": req.url,
                "netloc": req.netloc,
                "urlext": req.urlext,
                "status_code": req.status_code,
                "reason": req.reason,
                "verb": req.method,
                "initiator": req.initiator.to_json(full=False),
                "in_progress": req.in_progress,
                "last_update": req.last_update,
            }

        return payload
