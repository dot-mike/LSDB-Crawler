from __future__ import absolute_import, division, unicode_literals
import logging

from lsdbcrawler.items import FailedRequestItem
from lsdbcrawler.utils import randomProxy


from scrapy.exceptions import CloseSpider, IgnoreRequest
from scrapy.exceptions import NotConfigured
from scrapy.downloadermiddlewares.retry import RetryMiddleware, get_retry_request
from scrapy.utils.response import response_status_message

from twisted.internet import reactor
import twisted.internet.task


from scrapy.utils.project import get_project_settings


class HttpProxyMiddelware(object):
    def __init__(self, https=True):
        self.https = https

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings

        if not settings.getbool("PROXY_ENABLED", default=False):
            raise NotConfigured("HttpProxyMiddelware middleware is not enabled")

        https = settings.getbool("PROXY_HTTPS", default=True)

        middelware = cls(https=https)
        return middelware

    def process_request(self, request, spider):
        proxy_url = randomProxy(https=self.https)

        # Set the proxy
        request.meta["proxy"] = proxy_url
        logging.debug("Using proxy (scrapy request): %s", proxy_url)

    def process_exception(self, request, exception, spider):
        # What proxy had the exception
        proxy = request.meta["proxy"]

        logging.error("Exception using proxy %s: %s. %s", proxy, exception, request)


class DeferMiddleware(object):
    def process_request(self, request, spider):
        delay = request.meta.pop("__defer_delay", None)
        if not delay:
            return

        return twisted.internet.task.deferLater(reactor, delay, lambda: None)


class CustomRetryMiddleware(RetryMiddleware):
    def _retry(self, request, reason, spider):
        settings = spider.crawler.settings
        stats = spider.crawler.stats

        retry_times = request.meta.get("retry_times", 0) + 1
        max_retry_times = request.meta.get("max_retry_times", self.max_retry_times)
        priority_adjust = request.meta.get("priority_adjust", self.priority_adjust)

        last_proxy = request.meta.get("proxy")

        if last_proxy:
            logging.error(
                "Exception using proxy: %s, %s, %s", last_proxy, reason, request
            )

            # change proxy
            req = request.copy()
            req.meta["proxy"] = randomProxy(
                settings.getbool("PROXY_HTTPS", default=True)
            )
            req.dont_filter = True

        if retry_times <= max_retry_times:
            return get_retry_request(
                req,
                reason=reason,
                spider=spider,
                max_retry_times=max_retry_times,
                priority_adjust=priority_adjust,
            )

        else:
            # Create an item to store in MongoDB after 3 failed requests
            item = FailedRequestItem()
            item["url"] = request.url
            item["status"] = response_status_message(request.response.status)
            item["meta"] = request.meta
            yield item

            stats.inc_value("retry/max_reached")
            logging.error(
                "Gave up retrying %(request)s (failed %(retry_times)d times): "
                "%(reason)s",
                {"request": request, "retry_times": retry_times, "reason": reason},
                extra={"spider": spider},
            )
