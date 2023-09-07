import logging

logger = logging.getLogger()


def is_cloudsmith_url_valid(cloudsmith_url):
    try:
        import requests
    except ImportError:
        logging.error("Module 'requests' not found. Could not validate cloudsmith url.")
        return None
    response = requests.get(cloudsmith_url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to reach cloudsmith. Provided invalid URL: {cloudsmith_url}"
        )
