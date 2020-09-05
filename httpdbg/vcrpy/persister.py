# -*- coding: utf-8 -*-


class HTTPDBGPersister(object):
    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        raise ValueError(" -- useless for httpdbg -- ")

    @staticmethod
    def save_cassette(cassette_path, cassette_dict, serializer):
        pass
