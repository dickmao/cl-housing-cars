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
    def __init__(self, exporter, crawler):
        self.exporter = exporter
        self.settings = crawler.settings

    @classmethod
    def from_crawler(cls, crawler):
        exporter = next(x for x in crawler.extensions.middlewares if isinstance(x, FeedExporter))
        return cls(exporter=exporter, settings=crawler.settings)

    def process_item(self, item, spider):
        return item

