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
            "tag": req.tag,
            "initiator_id": req.initiator_id,
            "group_id": req.group_id,
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

        payload = {
            "id": records.id,
            "requests": {},
            "initiators": {},
            "groups": {},
        }

        for id, req in records.requests.items():
            payload["requests"][id] = {
                "id": req.id,
                "url": req.url,
                "netloc": req.netloc,
                "urlext": req.urlext,
                "status_code": req.status_code,
                "reason": req.reason,
                "verb": req.method,
                "tag": req.tag,
                "initiator_id": req.initiator_id,
                "group_id": req.group_id,
                "in_progress": req.in_progress,
                "tbegin": req.tbegin.isoformat(),
                "last_update": req.last_update.isoformat(),
            }

        for id, initiator in records.initiators.items():
            payload["initiators"][id] = initiator.to_json()

        for id, group in records.groups.items():
            payload["groups"][id] = group.to_json()

        return payload
