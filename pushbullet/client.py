import codecs
import json
from urllib.request import urlopen, Request


API_BASE_URL = "https://api.pushbullet.com/v2"


class Pushbullet:
    def __init__(self, access_token):
        self._auth_header = "Basic {}".format(codecs.encode("{}:".format(access_token).encode(), "base64").rstrip().decode())

    def push_note(self, title, body):
        self._do_post("pushes", json.dumps({"type": "note",
                                            "title": title,
                                            "body": body}))

    def push_link(self, title, url, body):
        self._do_post("pushes", json.dumps({"type": "link",
                                            "title": title,
                                            "url": url,
                                            "body": body}))

    # Private methods
    def _do_post(self, endpoint, body):
        try:
            response = urlopen(Request("{}/{}".format(API_BASE_URL, endpoint), body.encode(),
                                       {"Content-Type": "application/json",
                                        "Authorization": self._auth_header,
                                        "Length": len(body)}))
        except:
            raise

        response_object = json.loads(response.read().decode("utf-8"))

        if not response.status == 200:
            raise PushbulletError(response_object)


class PushbulletError(Exception):
    def __init__(self, error_object):
        self.message = "An error occurred while talking to Pushbullet: {}".format(error_object["error"]["message"])
        self.error_object = error_object

    def __str__(self):
        return self.message