import random
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import NotConfigured
from scrapy.exceptions import CloseSpider, IgnoreRequest


scrapy_settings = get_project_settings()
PROXY_LIST = scrapy_settings.get("PROXY_POOL")


def randomProxy(https=False):
    if not PROXY_LIST:
        raise NotConfigured("PROXY_POOL is not configured")

    try:
        proxy = random.choice(PROXY_LIST)
    except IndexError as exc:
        raise CloseSpider("No proxies available") from exc

    if https:
        proxy_url = "https://" + proxy
    else:
        proxy_url = "http://" + proxy

    return proxy_url
