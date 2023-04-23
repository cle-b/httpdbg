# -*- coding: utf-8 -*-
import httpx
import requests


def fnc_in_subpackage(url):
    requests.get(url)  # subpackage


class FakeClient:
    def navigate(self, url):
        requests.get(url)  # method


async def fnc_async(url):
    async with httpx.AsyncClient() as client:
        await client.get(url)
