import uuid
from urllib.parse import urlparse

from httpdbg.initiator import get_initiator


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
        self.initiator = None
        self.exception = None

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

    @property
    def status_code(self):
        code = 0
        if self.exception is not None:
            code = -1
        elif self.response is not None:
            code = self.response.status_code
        return code

    @property
    def reason(self):
        desc = "in progress"
        if self.exception is not None:
            desc = getattr(type(self.exception), "__name__", str(type(self.exception)))
        elif self.response is not None:
            desc = self.response.reason
        return desc

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

    @property
    def url(self):
        return self.request.url

    @property
    def netloc(self):
        url = urlparse(self.url)
        return f"{url.scheme}://{url.netloc}"

    @property
    def urlext(self):
        return self.url[len(self.netloc) :]


def set_hook(mixtape):
    """Intercepts the HTTP requests"""

    import requests

    mixtape.reset()

    requests.Session._original_send = requests.Session.send

    def _hook_send(session, request, **kwargs):

        record = HTTPRecord()
        record.initiator = get_initiator()
        record.request = request

        mixtape.requests[record.id] = record

        try:
            response = requests.Session._original_send(session, request, **kwargs)
        except Exception as ex:
            record.exception = ex
            raise

        record.response = response

        return response

    requests.Session.send = _hook_send


def unset_hook():

    import requests

    if getattr(requests.Session, "_original_send", None):
        requests.Session.send = requests.Session._original_send
