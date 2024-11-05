import os
from dotenv import load_dotenv

load_dotenv()

# Scrapy settings for ubb_threads project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

DEBUG = os.getenv("DEBUG", False)

BOT_NAME = "lsdbcrawler"

SPIDER_MODULES = ["lsdbcrawler.spiders"]
NEWSPIDER_MODULE = "lsdbcrawler.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0")

# MongoDB settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "lsdb")

# logging options
LOG_FILE = os.getenv("LOG_FILE", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_ENABLED = os.getenv("LOG_ENABLED", True)
LOG_STDOUT = os.getenv("LOG_STDOUT", True)
LOG_FILE_APPEND = False

# PROXY CONFIGURATION
PROXY_ENABLED = os.getenv("PROXY_ENABLED", False)
PROXY_HTTPS = os.getenv("PROXY_HTTPS", False)
# PROXY_POOL = ["user:pass@127.0.0.1:8080"]

proxy_file = os.getenv("PROXY_FILE", "proxies.txt")
if os.path.isfile(proxy_file):
    with open(proxy_file, mode="r", encoding="utf-8") as f:
        PROXY_POOL = f.read().splitlines()

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "lsdb")

# Obey robots.txt
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 10

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 10
# CONCURRENT_REQUESTS_PER_IP = 2

COOKIES_ENABLED = True

TELNETCONSOLE_ENABLED = True

DUPEFILTER_DEBUG = False

# Inrease if blocking IO is an issue
# https://docs.scrapy.org/en/latest/topics/settings.html#reactor-threadpool-maxsize
REACTOR_THREADPOOL_MAXSIZE = 100
DNS_TIMEOUT = 30

DOWNLOAD_TIMEOUT = 30

# Maximum document size, causes OOM kills if not set
DOWNLOAD_MAXSIZE = 10 * 1024 * 1024

# Print stats every 10 secs to console
LOGSTATS_INTERVAL = 10

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "lsdbcrawler.middlewares.HttpProxyMiddelware": 150,
    "lsdbcrawler.middlewares.DeferMiddleware": 200,
    "scrapy.downloadermiddlewares.redirect.RedirectMiddleware": 250,
    "lsdbcrawler.middlewares.CustomRetryMiddleware": 300,
}

DUPEFILTER_CLASS = "scrapy.dupefilters.RFPDupeFilter"

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "lsdbcrawler.pipelines.MongoPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 0.1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 30
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 10
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

RETRY_TIMES = 5
