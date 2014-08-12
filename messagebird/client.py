import json
import urllib.request

API_ENDPOINT_BASE = "https://rest.messagebird.com"


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
            request = urllib.request.Request(API_ENDPOINT_BASE + endpoint, body,
                                             {"Authorization": "AccessKey {}".format(self._api_key),
                                              "Accept": "application/json"}, method=method)
        except:
            raise

        response = urllib.request.urlopen(request)
        responseObject = json.loads(response.read().decode("utf-8"))

        if not response.getcode() in [200, 201]:
            raise MessageBirdError(responseObject)

        return responseObject


class MessageBirdError(Exception):
    def __init__(self, object):
        self.message = "There is an error in your entity: {}".format(object["errors"][0]["description"])
        self.object = object

    def __str__(self):
        return self.message