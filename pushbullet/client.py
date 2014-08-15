import json
import mimetypes
from pathlib import Path
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

    def push_file(self, file_path, body=None, mime_type=None):
        path = Path(file_path)
        file_name = path.parts[-1]

        if mime_type is None:
            mime_type = mimetypes.guess_type(file_path)

        # Request file upload
        response = self._request_upload(file_name, mime_type)

        # Upload file
        self._do_upload(file_path, response["upload_url"], response["data"])

        # Send push
        self._do_post("pushes", {"type": "file",
                                 "file_name": file_name,
                                 "file_type": mime_type,
                                 "file_url": response["file_url"],
                                 "body": body})

    # Private methods
    def _request_upload(self, file_name, mime_type):
        return self._do_post("upload-request", {"file_name": file_name,
                                                "file_type": mime_type})

    def _do_upload(self, file_path, upload_url, data):
        try:
            response = requests.post(upload_url, data, files={"file": open(file_path, "rb")})
        except:
            raise

        if not response.status_code == 204:
            response.raise_for_status()

    def _do_post(self, endpoint, body):
        try:
            body = json.dumps(body)

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