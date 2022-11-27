# -*- coding: utf-8 -*-
from httpdbg.hooks.httpx import unset_hook_for_httpx
from httpdbg.hooks.httpx import set_hook_for_httpx
from httpdbg.hooks.requests import unset_hook_for_requests
from httpdbg.hooks.requests import set_hook_for_requests


def set_hook_for_all_libs(records):
    set_hook_for_requests(records)
    set_hook_for_httpx(records)


def unset_hook_for_all_libs(records):
    unset_hook_for_requests(records)
    unset_hook_for_httpx(records)
