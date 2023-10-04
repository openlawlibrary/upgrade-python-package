import os

import pip._vendor.requests as requests

from .exceptions import SlackError


class SlackNotifier:
    def __init__(self, token):
        self.url = token

    def post_message(self, header, text):
        data = f'{{"attachments": [{{"color": "danger", "pretext": "*{header}*", "text":"{text}"}}]}}'
        return requests.post(self.url, data=data)


def send_slack_notification(header, text, token):
    """Posts a slack message to a specific channel determined by slack webhook url."""
    if token is None:
        token = os.environ.get("SLACK_WEBHOOK_URL")

    notifier = SlackNotifier(token)
    try:
        notifier.post_message(header, text)
    except Exception as e:
        raise SlackError(f"Could not send slack notification due to error {e}")
