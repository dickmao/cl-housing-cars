# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.extensions.feedexport import FeedExporter
import os, pickle
from pytz import utc
import dateutil.parser

class SomePipeline(object):
    def __init__(self, exporter):
        self.exporter = exporter

    @classmethod
    def from_crawler(cls, crawler):
        return cls(exporter=next(x for x in crawler.extensions.middlewares if isinstance(x, FeedExporter)))

    def process_item(self, item, spider):
        return item

    def close_spider(self,spider):
        stamp = dateutil.parser.parse(self.exporter.slot.storage.keyname \
                                      .split(".")[1][::-1].replace("-", ":", 2)[::-1]) \
                               .replace(tzinfo=utc);
        restore = self.exporter.slot.storage.keyname
        self.exporter.slot.storage.keyname = "marker1.pkl"
        file = self.exporter.slot.storage.open(spider)
        pickle.dump(stamp, file)
        self.exporter.slot.storage.store(file)
        self.exporter.slot.storage.keyname = restore
