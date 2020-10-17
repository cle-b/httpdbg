# -*- coding: utf-8 -*-
import sys

import requests

base_url = sys.argv[1]

_ = requests.get(f"{base_url}/get")
_ = requests.post(f"{base_url}/post")
