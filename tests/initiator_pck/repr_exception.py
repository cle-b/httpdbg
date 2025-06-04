import requests


class BrokenREPR:

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        boum  # noqa F821


def get(br):
    requests.get(br.url)
