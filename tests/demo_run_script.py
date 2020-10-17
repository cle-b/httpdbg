# -*- coding: utf-8 -*-
import sys

import requests

base_url = sys.argv[1]

_ = requests.get(f"{base_url}/get")

if len(sys.argv) == 3:
    if sys.argv[2] == "raise_exception":
        raise Exception("--raise_exception--")

_ = requests.post(f"{base_url}/post")
