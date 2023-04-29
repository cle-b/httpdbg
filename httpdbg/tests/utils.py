# -*- coding: utf-8 -*-
import requests


def get_request_details(current_httpdbg_port, req_number):
    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    req_id = reqs[list(reqs.keys())[req_number]]["id"]
    return requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/{req_id}")


def get_request_content_up(current_httpdbg_port, req_number):
    ret = requests.get(f"http://127.0.0.1:{current_httpdbg_port}/requests")

    reqs = ret.json()["requests"]

    req_id = reqs[list(reqs.keys())[req_number]]["id"]
    return requests.get(f"http://127.0.0.1:{current_httpdbg_port}/request/{req_id}/up")
