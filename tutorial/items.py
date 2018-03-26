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
    id = scrapy.Field()
    price = scrapy.Field()
    link = scrapy.Field()
    desc = scrapy.Field()
    coords = scrapy.Field()
    listedby = scrapy.Field()
    attrs = scrapy.Field()
    posted = scrapy.Field(serializer=lambda x: x.isoformat())
    updated = scrapy.Field(serializer=lambda x: x.isoformat())
    image_urls = scrapy.Field()

class JoineryItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    id = scrapy.Field()
    desc = scrapy.Field()
    listedby = scrapy.Field()

class ListingsProjectItem(scrapy.Item):
    desc = scrapy.Field()
    link = scrapy.Field()
    title = scrapy.Field()
    id = scrapy.Field()
    listedby = scrapy.Field()
    coords = scrapy.Field()
    posted = scrapy.Field()
    updated = scrapy.Field()
    price = scrapy.Field()
