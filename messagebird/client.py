import json
from urllib.request import urlopen, Request

API_BASE_URL = "https://rest.messagebird.com"


class MessageBird:
    def __init__(self, api_key):
        self._api_key = api_key

    def send_message(self, body=None, originator=None, recipients=None, message=None):
        if message is None:
            message = json.dumps({"originator": originator,
                                  "recipients": recipients if isinstance(recipients, list) else [recipients],
                                  "body": body})

        try:
            return self._do_http("POST", "/messages", message)
        except:
            raise

    #
    # Private methods
    #
    def _do_http(self, method, endpoint, body=None):
        try:
            response = urlopen(Request("{}/{}".format(API_BASE_URL, endpoint), body.encode(),
                                       {"Authorization": "AccessKey {}".format(self._api_key),
                                        "Accept": "application/json",
                                        "Length": len(body)}, method=method))
        except:
            raise

        response_object = json.loads(response.read().decode("utf-8"))

        if not response.status in [200, 201]:
            raise MessageBirdError(response_object)

        return response_object


class MessageBirdError(Exception):
    def __init__(self, error_object):
        self.message = "There is an error in your entity: {}".format(error_object["errors"][0]["description"])
        self.error_object = error_object

    def __str__(self):
        return self.message