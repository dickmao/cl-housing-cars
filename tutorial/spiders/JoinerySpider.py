from tutorial.items import JoineryItem
from scrapy import Request
from scrapy.utils.response import get_base_url
from .BaseSpider import BaseSpider
import pickle


class JoinerySpider(BaseSpider):
    name = "joinery"
    allowed_domains = ["joinery.nyc"]
    start_urls = [
        "https://joinery.nyc/apt-for-rent?bedrooms=Bedrooms&date=&listing-type=Apartment+Type&page=0&price-high=Max+%24&price-low=Min+%24&utf8=%E2%9C%93",
    ]

    def __init__(self, name=None, **kwargs):
        super(JoinerySpider, self).__init__(name, **kwargs)
        self.new_top_urls = []

    def _set_crawler(self, crawler):
        super(JoinerySpider, self)._set_crawler(crawler)
        self.old_top_urls = self.download_s3(self.Marker) if self.Marker else []
        self.set_old_top_urls = set(self.old_top_urls)

    def parse_text(self, response):
        item = JoineryItem()
        item['desc'] = ' '.join(response.xpath('//div[@class="managed"]/*[not(self::h3)]/text()').extract())
        item['link'] = get_base_url(response)
        item['title'] = response.xpath('//title/text()').extract_first().replace('\n', '')
        item['id'] = response.xpath('//div[@class="thumbnail-gallery"]/div[1]/@data-listing').extract_first()
        item['listedby'] = response.xpath('//div[@class="listing-owner-name"]/text()').extract_first().replace('\n', '')
        if item['desc']:
            yield item

    def parse(self, response):
        first = True
        for rrow in response.xpath('//section[@data-highlight-map-id]/header[@class="listing-header"]//a'):
            href = rrow.xpath('./@href').extract_first()
            url = response.urljoin(href)
            if self.gone_back_enough(url):
                return
            if first:
                self.new_top_urls.append(url)
                first = False
            yield Request(url, self.parse_text)
        next_page = response.xpath('//a[@rel="next"]/@href').extract_first()
        if next_page:
            url = response.urljoin(next_page)
            yield Request(url, self.parse)

    def gone_back_enough(self, url):
        return url in self.set_old_top_urls

    def closed(self, reason):
        super(JoinerySpider, self).closed(reason)
        if self.exporter.slot.itemcount:
            to_save = (self.new_top_urls + self.old_top_urls)[0:10]
            file = self.storage.open(self)
            pickle.dump(to_save, file)
            marker = self.settings['MARKER'] % self.exporter._get_uri_params(self)
            self.upload_s3(marker, file)
