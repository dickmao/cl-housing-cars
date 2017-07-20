# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.extensions.feedexport import FeedExporter
import os

class SomePipeline(object):
    def __init__(self, exporter):
        self.exporter = exporter

    @classmethod
    def from_crawler(cls, crawler):
        return cls(exporter=next(x for x in crawler.extensions.middlewares if isinstance(x, FeedExporter)))

    def process_item(self, item, spider):
        return item

    def close_spider(self,spider):
        slink = '%s/%s' % (os.path.dirname(self.exporter.slot.file.name), 'marker1')
        try:
            os.unlink(slink)
        except OSError:
            pass
        os.symlink(os.path.basename(self.exporter.slot.file.name), slink)
