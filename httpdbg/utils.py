# -*- coding: utf-8 -*-
import logging
import secrets
import os
import string


def get_new_uuid():
    # important - the uuid must be compatible with method naming rules
    return "".join(secrets.choice(string.ascii_letters) for i in range(10))


logger = logging.getLogger("httpdbg")
logger.setLevel(100)
log_level = os.environ.get("HTTPDBG_LOG")
if log_level is not None:
    logging.basicConfig(level=int(log_level), format="%(message)s")
    logger.setLevel(int(log_level))
