import json
import http.client

API_ENDPOINT = "rest.messagebird.com"


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
            client = http.client.HTTPSConnection(API_ENDPOINT, 443)

            client.request(method, endpoint, body, {"Authorization": "AccessKey {}".format(self._api_key),
                                                    "Accept": "application/json"})
            response = client.getresponse()
        except:
            raise

        response_object = json.loads(response.read().decode("utf-8"))

        if not response.getcode() in [200, 201]:
            raise MessageBirdError(response_object)

        return response_object


class MessageBirdError(Exception):
    def __init__(self, error_object):
        self.message = "There is an error in your entity: {}".format(error_object["errors"][0]["description"])
        self.error_object = error_object

    def __str__(self):
        return self.message