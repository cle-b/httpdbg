# -*- coding: utf-8 -*-
from httpdbg.hooks.aiohttp import unset_hook_for_aiohttp
from httpdbg.hooks.aiohttp import set_hook_for_aiohttp
from httpdbg.hooks.httpx import unset_hook_for_httpx
from httpdbg.hooks.httpx import set_hook_for_httpx
from httpdbg.hooks.httpclient import set_hook_for_httpclient
from httpdbg.hooks.httpclient import unset_hook_for_httpclient


def set_hook_for_all_libs(records):
    set_hook_for_aiohttp(records)
    set_hook_for_httpx(records)
    set_hook_for_httpclient(records)


def unset_hook_for_all_libs(records):
    unset_hook_for_aiohttp(records)
    unset_hook_for_httpx(records)
    unset_hook_for_httpclient(records)
