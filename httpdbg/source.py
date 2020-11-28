# -*- coding: utf-8 -*-
import secrets
import string


def uuid(length=6):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Source(object):
    def __init__(self, label):
        self.id = uuid()
        self.label = label

    def to_json(self):
        return {"id": self.id, "label": self.label}
