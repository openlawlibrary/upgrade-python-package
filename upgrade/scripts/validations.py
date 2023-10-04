import logging

logger = logging.getLogger(__name__)


def is_cloudsmith_url_valid(cloudsmith_url: str) -> None:
    import pip._vendor.requests as requests

    response = requests.head(cloudsmith_url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to reach package index url. Provided invalid URL: {cloudsmith_url}"
        )
