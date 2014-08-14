import json
import requests
from requests.auth import HTTPBasicAuth

API_BASE_URL = "https://api.pushbullet.com/v2"


class Pushbullet:
    def __init__(self, access_token):
        self._access_token = access_token

    def push_note(self, title, body):
        self._do_post("pushes", {"type": "note",
                                 "title": title,
                                 "body": body})

    def push_link(self, url, title, body):
        self._do_post("pushes", {"type": "link",
                                 "title": title,
                                 "url": url,
                                 "body": body})

    def push_file(self, file_path, mime_type, body):
        response = self._request_upload(file_path, mime_type)

    # Private methods
    def _request_upload(self, file_path, mime_type):
        pass

    def _do_post(self, endpoint, body):
        try:
            body = json.dumps(body).encode("utf-8")

            response = requests.post("{}/{}".format(API_BASE_URL, endpoint), body,
                                     auth=HTTPBasicAuth(self._access_token, ""),
                                     headers={"Content-Type": "application/json"})
        except:
            raise

        response_object = response.json()

        if not response.status_code == 200:
            raise PushbulletError(response_object)

        return response_object


class PushbulletError(Exception):
    def __init__(self, error_object):
        self.message = "An error occurred while talking to Pushbullet: {}".format(error_object["error"]["message"])
        self.error_object = error_object

    def __str__(self):
        return self.message