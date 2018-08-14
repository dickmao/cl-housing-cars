# -*- coding: utf-8 -*-

# Scrapy settings for tutorial project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import os, boto3, socket
from contextlib import closing

# https://stackoverflow.com/users/715042/michael
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.settimeout(6)
            ret = sock.connect_ex((host, port))
            return ret == 0
        except:
            return False

q_scrapoxy = check_socket('scrapoxy', 8888)
q_redis = check_socket('redis', 6379)
credentials = boto3.Session().get_credentials()

LOG_LEVEL = 'INFO'
BOT_NAME = 'tutorial'
SPIDER_MODULES = ['tutorial.spiders']
NEWSPIDER_MODULE = 'tutorial.spiders'
DOWNLOAD_HANDLERS = {
#  's3': 'scrapy.core.downloader.handlers.s3.S3DownloadHandler',
}

AWS_ACCESS_KEY_ID = credentials.access_key
AWS_SECRET_ACCESS_KEY = credentials.secret_key
AWS_ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']
REDIS_HOST = "redis" if q_redis else "localhost"
FEED_URI = "s3x://{}.%(name)s/Data.%(timestamp)s.json".format(AWS_ACCOUNT_ID)
FEED_TEMPDIR = "/var/tmp"
FEED_STORAGES = {
    's3x': 'tutorial.feedstorage.S3FeedStorage',
}
MARKER_DIR = "{}/{}/%(name)s".format("/var/lib/scrapyd/items" if os.path.isdir("/var/lib/scrapyd") else "/var/tmp", BOT_NAME)
MARKER = "Marker.%(timestamp)s.json"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'tutorial (+http://www.yourdomain.com)'
DOWNLOAD_FAIL_ON_DATALOSS = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS=32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY=1
RETRY_TIMES = 0
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN=1
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
COOKIES_ENABLED=False

if q_scrapoxy:
    PROXY = 'http://scrapoxy:8888/?noconnect'
    API_SCRAPOXY = 'http://scrapoxy:8889/api'
    API_SCRAPOXY_PASSWORD = os.environ.get('API_SCRAPOXY_PASSWORD')
    if not API_SCRAPOXY_PASSWORD:
        raise

BLACKLIST_HTTP_STATUS_CODES = [ 403 ]

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'tutorial.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
if q_scrapoxy:
    WAIT_FOR_SCALE = 300
    DOWNLOADER_MIDDLEWARES = {
    #    'tutorial.middlewares.MyCustomDownloaderMiddleware': 543,
        'scrapoxy.downloadmiddlewares.proxy.ProxyMiddleware': 100,
        'scrapoxy.downloadmiddlewares.wait.WaitMiddleware': 101,
        'scrapoxy.downloadmiddlewares.scale.ScaleMiddleware': 102,
        'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
        'scrapoxy.downloadmiddlewares.blacklist.BlacklistDownloaderMiddleware': 950,
    }

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'tutorial.pipelines.SomePipeline': 300,
    #    'tutorial.pipelines.images.ImagesPipeline': 1
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
#AUTOTHROTTLE_ENABLED=True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED=True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'
