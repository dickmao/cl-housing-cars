from tutorial.items import ListingsProjectItem
from datetime import date, timedelta
from .BaseSpider import BaseSpider
import json, pickle


class ListingsProjectSpider(BaseSpider):
    name = "listingsproject"
    allowed_domains = ["listingsproject.com"]
    start_urls = []

    @staticmethod
    def _wednesday(adate):
        while adate.weekday() != 2:
            adate -= timedelta(days=1)
        return adate

    def __init__(self, name=None, **kwargs):
        super(ListingsProjectSpider, self).__init__(name, **kwargs)
        self.wednesdays = [self._wednesday(date.today() - timedelta(days=1+7*i))
                           for i in range(4)]

    def _set_crawler(self, crawler):
        super(ListingsProjectSpider, self)._set_crawler(crawler)
        old_wednesdays = self.download_s3(self.Marker) if self.Marker else []
        for w in self.wednesdays:
            if w not in old_wednesdays:
                self.start_urls.append("https://www.listingsproject.com/newsletter/{}/new-york-city".format(w))

    def closed(self, reason):
        if self.exporter.slot.itemcount:
            file = self.storage.open(self)
            pickle.dump(self.wednesdays, file)
            marker = self.settings['MARKER'] % self.exporter._get_uri_params(self)
            self.upload_s3(marker, file)

    def parse(self, response):
        item = ListingsProjectItem()
        blob = json.loads(response.xpath('//div/@data-react-props').extract_first())
        for listing in blob['initialListings']:
            # I don't use listing.get('about_you', '') because the entry always exists and its value is often None
            item['desc'] = listing['description'] + '\n' + (listing.get('about_you') or "")
            item['link'] = response.urljoin("listing/{}".format(listing['slug']))
            item['title'] = listing['headline']
            item['id'] = listing['id']
            item['listedby'] = listing['name']
            if item['desc']:
                yield item
