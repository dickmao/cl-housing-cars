from .BaseSpider import BaseSpider
import redis, sys

class DeadSpider(BaseSpider):
    name = "dead"
    allowed_domains = []

    def __init__(self, name=None, **kwargs):
        super(DeadSpider, self).__init__(name, **kwargs)
        self.link2dbitem = dict()
        self.dels = []

    def _set_crawler(self, crawler):
        super(DeadSpider, self)._set_crawler(crawler)
        for db in range(11):
            red = redis.StrictRedis(host=self.settings['REDIS_HOST'], db=db)
            try:
                for i in red.zscan_iter('item.index.score'):
                    link = red.hget("item.{}".format(i[0]), 'link')
                    self.start_urls.append(link)
                    self.link2dbitem[link] = (db, i[0])
            except redis.exceptions.ConnectionError as e:
                self.logger.warning("db={} {}".format(db, e))
                next

    def parse(self, response):
        if (bool(response.xpath('//section[@class="body"]//div[@class="removed"]')) or
            bool(response.xpath('//body//p/text()[contains(translate(., "ERO", "ero"), "404 error")]'))):
            self.dels.append(response.url)

    def closed(self, reason):
        super(DeadSpider, self).closed(reason)

        bydb = [[] for _ in xrange(11)]
        for url in self.dels:
            (db, id) = self.link2dbitem[url]
            bydb[db].append(id)

        for db,ids in enumerate(bydb):
            if ids:
                red = redis.StrictRedis(host=self.settings['REDIS_HOST'], db=db)
                red.delete(*["item.{}".format(i) for i in ids])
                red.zrem("item.index.price", *ids)
                red.zrem("item.index.bedrooms", *ids)
                red.zrem("item.index.score", *ids)
                red.zrem("item.geohash.coords", *ids)
                for i in range(30):
                    red.zrem("item.index.posted.{}".format(i), *ids)
