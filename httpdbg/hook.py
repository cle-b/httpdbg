import uuid


class HTTPRecords:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.requests = {}

    def reset(self):
        self.id = str(uuid.uuid4())
        self.requests = {}


class HTTPRecord:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.unread = True
        self._request = None
        self._response = None
        self.src = None

    @property
    def request(self):
        self.unread = False
        return self._request

    @request.setter
    def request(self, r):
        self.unread = True
        self._request = r

    @property
    def response(self):
        self.unread = False
        return self._response

    @response.setter
    def response(self, r):
        self.unread = True
        self._response = r

    @staticmethod
    def list_headers(headers):
        lst = []
        for name, value in headers.items():
            lst.append({"name": name, "value": value})
        return lst

    @staticmethod
    def get_header(headers, name):
        for _name, value in headers.items():
            if _name.lower() == name.lower():
                return value
        return ""


def set_hook(mixtape):
    """Intercepts the HTTP requests"""

    import requests

    mixtape.reset()

    requests.Session._original_send = requests.Session.send

    def _hook_send(session, request, **kwargs):

        record = HTTPRecord()
        record.request = request

        mixtape.requests[record.id] = record

        response = requests.Session._original_send(session, request, **kwargs)

        record.response = response

        return response

    requests.Session.send = _hook_send


def unset_hook():

    import requests

    if getattr(requests.Session, "_original_send", None):
        requests.Session.send = requests.Session._original_send
