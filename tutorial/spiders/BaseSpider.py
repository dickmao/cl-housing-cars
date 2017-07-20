from scrapy import Request
from scrapy.spiders import Spider
from scrapy.utils.response import get_base_url
from tutorial.items import DmozItem
from scrapy.shell import inspect_response
from sys import exit

class BaseSpider(Spider):
    allowed_domains = ["craigslist.org"]
    start_urls = []

    def parse_text(self, response):
        item = DmozItem()
        item['desc'] = ' '.join(response.xpath('//section[@id="postingbody"]/text()').extract())
        item['link'] = get_base_url(response)
        item['title'] = response.xpath('//title/text()').extract_first()
        coords = response.xpath('//div[@class="mapAndAttrs"]/div[@class="mapbox"]/div[@id="map"]')
        item['coords'] = (coords.xpath('./@data-latitude').extract_first(),
                          coords.xpath('./@data-longitude').extract_first())
        item['listedby'] = response.xpath('//div[@class="mapAndAttrs"]/p[@class="attrgroup"]/span[contains(.//text(), "listed")]/b/text()').extract_first()
        # item['title'] = sel.xpath('a/text()').extract()
        # item['link'] = sel.xpath('a/@href').extract()
        # item['desc'] = sel.xpath('text()').extract()
        if item['desc']:
            yield item

    def parse(self, response):
        stopat = response.xpath('//h4[@class="ban nearby"]/following-sibling::li//@data-pid').extract_first()
        for rrow in response.xpath('//div[@class="content"]//li[@class="result-row"]'):
            pid = rrow.xpath('.//@data-pid').extract_first()
            if pid == stopat:
                break
            href = rrow.xpath('.//@href').extract_first()
            url = response.urljoin(href)
            yield Request(url, self.parse_text)
        next_page = response.xpath('//a[@class="button next"]//@href').extract_first()
        if next_page:
            url = response.urljoin(next_page)
            yield Request(url, self.parse)
