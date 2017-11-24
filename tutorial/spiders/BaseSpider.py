from scrapy import Request
from scrapy.spiders import Spider
from scrapy.utils.response import get_base_url
from tutorial.items import DmozItem
from scrapy.shell import inspect_response
from sys import exit
from urlparse import urlparse, parse_qsl, urlunparse
from urllib import urlencode
from datetime import datetime
from pytz import utc
from collections import Callable
import dateutil.parser
import json, glob, os, threading, re

# Cole Maclean
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return (datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

class CallableParseLink(Callable):
    def __init__(self, spider, url):
        self._spider = spider
        self._url = url
        
    def __call__(self, response):
        ban = response.xpath('//h4[@class="ban nearby"]/following-sibling::li//@data-pid').extract_first()
        queue = []
        for rrow in response.xpath('//div[@class="content"]//li[@class="result-row"]'):
            pid = rrow.xpath('.//@data-pid').extract_first()
            if pid == ban:
                break
            href = rrow.xpath('.//@href').extract_first()
            queue.append(response.urljoin(href))
        if queue:
            next_page = response.xpath('//a[@class="button next"]//@href').extract_first()
            yield Request(queue[0], CallableParseText(self._spider, self._url, queue[1:], response.urljoin(next_page) if next_page else None))

class CallableParseText(Callable):
    def __init__(self, spider, url, queue, next_page):
        self._spider = spider
        self._url = url
        self._queue = queue
        self._next_page = next_page
        
    def __call__(self, response):
        isodates = response.xpath('//div[@class="postinginfos"]//time[@class="date timeago"]/@datetime').extract()
        if not self._spider.states[self._url]._current_posted:
            # we're in the first page of results
            self._spider.states[self._url]._current_posted = dateutil.parser.parse(isodates[-1])
        if not self._spider.gone_back_enough(dateutil.parser.parse(isodates[-1]), self._url):
            item = DmozItem()
            item['desc'] = ' '.join(response.xpath('//section[@id="postingbody"]/text()').extract())
            item['link'] = get_base_url(response)
            item['title'] = response.xpath('//span[@id="titletextonly"]/text()').extract_first() + response.xpath('//span[@class="postingtitletext"]/small/text()').extract_first()
            item['id'] = re.findall(r"(\d+)", response.xpath('//div[@class="postinginfos"]//p[@class="postinginfo"]/text()').extract_first())[-1]
            item['price'] = response.xpath('//section[@class="body"]//span[@class="price"]/text()').extract_first()
            coords = response.xpath('//div[@class="mapbox"]/div[@id="map"]')
            item['coords'] = (coords.xpath('./@data-latitude').extract_first(),
                              coords.xpath('./@data-longitude').extract_first())
            item['posted'] = dateutil.parser.parse(isodates[0])
            item['updated'] = dateutil.parser.parse(isodates[-1])

            item['attrs'] = []
            for span in response.xpath('//div[@class="mapAndAttrs"]//p[@class="attrgroup"]/span'):
                item['attrs'].append(' '.join(span.xpath('.//text()').extract()))

            # item['listedby'] = response.xpath('//div[@class="mapAndAttrs"]/p[@class="attrgroup"]/span[contains(.//text(), "listed")]/b/text()').extract_first()
            # item['title'] = sel.xpath('a/text()').extract()
            # item['link'] = sel.xpath('a/@href').extract()
            # item['desc'] = sel.xpath('text()').extract()
            item['image_urls'] = []
            for thumb in response.xpath('//div[@id="thumbs"]//img'):
                item['image_urls'].append(thumb.xpath('.//@src').extract_first())
            if item['desc']:
                yield item
            if self._queue:
                yield Request(self._queue[0], CallableParseText(self._spider, self._url, self._queue[1:], self._next_page))
            elif self._next_page:
                yield Request(self._next_page, CallableParseLink(self._spider, self._url))

class TopLevelState:
    def __init__(self, url):
        self._url = url
        self._lock = threading.Lock()
        self._current_posted = None
        self._prev_posted = utc.localize(datetime.min)

    def __hash__(self):
        return hash(self.url)
    def __eq__(self, other):
        return self._url == other._url
    
    def update(self, **kwargs):
        for k,v in kwargs.iteritems():
            try:
                self.k = v
            except AttributeError:
                raise AttributeError
                
    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

class BaseSpider(Spider):
    allowed_domains = ["craigslist.org"]
    start_urls = []
    
    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name, **kwargs)
        self.timestamp = datetime.utcnow().replace(microsecond=0).isoformat().replace(':', '-')
        self.states = dict()

    def _set_crawler(self, crawler):
        super(BaseSpider, self)._set_crawler(crawler)
        fmarkers = list(glob.iglob(self.settings['MARKER'] % { 'name': self.name, 'timestamp': '*' }))
        if fmarkers:
            with open(max(fmarkers), 'r') as fp:
                self.marker = json.load(fp)
                for k,v in self.marker.iteritems():
                    self.states[k] = self.states.get(k, TopLevelState(k))
                    if v:
                        self.states[k]._prev_posted = dateutil.parser.parse(v)

    def closed(self, reason):
        fmarker = self.settings['MARKER'] % { 'name': self.name, 'timestamp': self.timestamp }
        with open(fmarker, 'w') as fp:
            json.dump({ v._url: (v._current_posted if v._current_posted else v._prev_posted) for v in self.states.values() }, fp, indent=4, cls=DateTimeEncoder)
        
    def parse(self, response):
        url = get_base_url(response)
        nabes = set()
        for input in response.xpath('//input[@name="nh"]'):
            nabes.add(input.xpath('./@value').extract_first())
        if nabes:
            parsed = urlparse(url)
            for nabe in nabes:
                query = dict(parse_qsl(parsed.query))
                query["nh"] = nabe
                # _replace is part of namedtuple public API, says Nigel Tufnel
                parsed = parsed._replace(query=urlencode(query))
                #                stopat = get latestfrom the shit
                url = urlunparse(parsed)
                self.states[url] = self.states.get(url, TopLevelState(url))
                yield Request(url, CallableParseLink(self, url))
        else:
            self.states[url] = self.states.get(url, TopLevelState(url))
            yield Request(url, CallableParseLink(self, url))
                
    def gone_back_enough(self, dt, url):
        return dt < self.states[url]._prev_posted
        
