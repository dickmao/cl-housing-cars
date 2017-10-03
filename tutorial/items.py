# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join

class DmozItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()
    coords = scrapy.Field()
    attrs = scrapy.Field()
    posted = scrapy.Field()
    updated = scrapy.Field()
    image_urls = scrapy.Field()
