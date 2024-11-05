import os
import pytest
import unittest
from scrapy.settings import Settings
from scrapy.http import HtmlResponse
from lsdbcrawler.spiders.liveset_spider import LivesetSpider

from unittest.mock import MagicMock, patch
from scrapy.http import HtmlResponse

@pytest.fixture(scope='module')
def lsdb():
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    return HtmlResponse(
        url="https://lsdb.eu/livesets",
        body=open(
            os.path.join(__location__, "response/livesets_index.html"), mode="rb"
        ).read(),
        encoding="utf-8",
    )

@pytest.fixture(autouse=True, scope='class')
def _request_lsdb_page(request, lsdb):
    request.cls._response = lsdb

class TestLivesetSpider(unittest.TestCase):
    def setUp(self):
        self.spider = LivesetSpider()
        self.spider.settings = Settings()

    def test_parse_livesets_index_with_livesets(self):
        generator = self.spider.parse_livesets_index(self._response)
        requests = list(generator)
        self.assertEqual(len(requests), 51)

    def test_parse_livesets_index_restart(self):
        generator = self.spider.parse_livesets_index(self._response, restart=True, restart_count=5)
        requests = list(generator)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].url, 'https://lsdb.eu/livesets?page=2')

    @patch.object(HtmlResponse, 'xpath', return_value=[])
    def test_parse_livesets_index_no_livesets(self, mock_xpath):
        generator = self.spider.parse_livesets_index(self._response)
        requests = list(generator)
        self.assertEqual(len(requests), 1)




