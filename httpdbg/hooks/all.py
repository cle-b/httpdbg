# -*- coding: utf-8 -*-
from httpdbg.hooks.aiohttp import unset_hook_for_aiohttp
from httpdbg.hooks.aiohttp import set_hook_for_aiohttp
from httpdbg.hooks.httpx import unset_hook_for_httpx
from httpdbg.hooks.httpx import set_hook_for_httpx
from httpdbg.hooks.requests import unset_hook_for_requests
from httpdbg.hooks.requests import set_hook_for_requests
from httpdbg.hooks.urllib3 import unset_hook_for_urllib3
from httpdbg.hooks.urllib3 import set_hook_for_urllib3


def set_hook_for_all_libs(records):
    set_hook_for_aiohttp(records)
    set_hook_for_requests(records)
    set_hook_for_httpx(records)
    set_hook_for_urllib3(records)


def unset_hook_for_all_libs(records):
    unset_hook_for_aiohttp(records)
    unset_hook_for_requests(records)
    unset_hook_for_httpx(records)
    unset_hook_for_urllib3(records)
