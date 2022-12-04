# -*- coding: utf-8 -*-
import secrets
import string


def get_new_uuid():
    # important - the uuid must be compatible with method naming rules
    return "".join(secrets.choice(string.ascii_letters) for i in range(10))
