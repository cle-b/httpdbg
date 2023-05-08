# -*- coding: utf-8 -*-
from json import JSONEncoder
from typing import Any
from typing import Dict

from httpdbg.records import HTTPRecords
from httpdbg.records import HTTPRecord


class RequestPayload(JSONEncoder):
    def default(self, req: HTTPRecord) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
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
            payload["request"]["body"] = {
                "path": f"/request/{req.id}/up",
                "filename": "upload",
            }
            payload["request"]["body"].update(req.request.preview)

        payload["response"] = {
            "headers": [header.to_json() for header in req.response.headers],
            "cookies": [cookie.to_json() for cookie in req.response.cookies],
        }

        if req.response.content:
            payload["response"]["body"] = {
                "path": f"/request/{req.id}/down",
                "filename": "download",
            }
            payload["response"]["body"].update(req.response.preview)

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
