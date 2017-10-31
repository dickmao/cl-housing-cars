# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.extensions.feedexport import FeedExporter
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

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
        dedupe_script = os.path.join(spider.settings['PARENT_DIR'], "dedupe.py")
        try:
            dedupe_dir = os.path.dirname(spider.settings['FEED_URI']) % self.exporter._get_uri_params(spider)
            logger.info("Running {} {}".format(dedupe_script, dedupe_dir))
            subprocess.check_call([dedupe_script, dedupe_dir])
        except subprocess.CalledProcessError as e:
            logger.error("{}: {}".format(dedupe_script, str(e)))
