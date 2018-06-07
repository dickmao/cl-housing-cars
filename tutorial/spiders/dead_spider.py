from .BaseSpider import BaseSpider
import redis, pickle, os

class DeadSpider(BaseSpider):
    name = "dead"
    allowed_domains = []

    def __init__(self, name=None, **kwargs):
        super(DeadSpider, self).__init__(name, **kwargs)
        self.link2dbitem = dict()
        self.dels = []
        self.last_id = ""

    def _add_links(self):
        start_adding = not(bool(self.last_id))
        for db in range(11):
            if len(self.start_urls) >= 100:
                break
            red = redis.StrictRedis(host=self.settings['REDIS_HOST'], db=db)
            try:
                for i in red.zscan_iter('item.index.score'):
                    if start_adding:
                        link = red.hget("item.{}".format(i[0]), 'link')
                        self.start_urls.append(link)
                        self.link2dbitem[link] = (db, i[0])
                        if len(self.start_urls) >= 100:
                            self.last_id = i[0]
                            break
                    else:
                        start_adding = self.last_id == i[0]
            except redis.exceptions.ConnectionError as e:
                self.logger.warning("db={} {}".format(db, e))
                next

    def _set_crawler(self, crawler):
        super(DeadSpider, self)._set_crawler(crawler)
        try:
            self.last_id = pickle.load(open(os.path.join(self.marker_dir, 'last-id.pkl'), 'r'))
        except IOError:
            self.last_id = ""
        self._add_links
        # Not enough (self.last_id not found or tail end).
        # In either case, last_id is True
        # Could result in overlap-around, but won't be for more than 100
        if len(self.start_urls) < 100 and self.last_id:
            self.last_id = ""
            self._add_links

    def parse(self, response):
        if (bool(response.xpath('//section[@class="body"]//div[@class="removed"]')) or
            bool(response.xpath('//body//p/text()[contains(translate(., "ERO", "ero"), "404 error")]'))):
            self.dels.append(response.url)

    def closed(self, reason):
        super(DeadSpider, self).closed(reason)

        with open(os.path.join(self.marker_dir, 'last-id.pkl'), 'w+') as fp:
            pickle.dump(self.last_id, fp)

        bydb = [[] for _ in xrange(11)]
        for url in self.dels:
            (db, id) = self.link2dbitem[url]
            bydb[db].append(id)

        for db,ids in enumerate(bydb):
            if ids:
                self.logger.info("Deleting db={} {}".format(db, ', '.join(ids)))
                red = redis.StrictRedis(host=self.settings['REDIS_HOST'], db=db)
                red.delete(*["item.{}".format(i) for i in ids])
                red.zrem("item.index.price", *ids)
                red.zrem("item.index.bedrooms", *ids)
                red.zrem("item.index.score", *ids)
                red.zrem("item.geohash.coords", *ids)
                for i in range(30):
                    red.zrem("item.index.posted.{}".format(i), *ids)
