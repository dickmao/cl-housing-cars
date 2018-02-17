from scrapy.extensions.feedexport import FeedExporter
from scrapy.spiders import Spider
from datetime import datetime
import pickle, os

class BaseSpider(Spider):
    """Provides common code for s3 uploaders/downloaders."""

    def __init__(self, name=None, **kwargs):
        super(BaseSpider, self).__init__(name, **kwargs)
        self.timestamp = datetime.utcnow().replace(microsecond=0).isoformat().replace(':', '-')
        self.Marker = ''

    def _set_crawler(self, crawler):
        super(BaseSpider, self)._set_crawler(crawler)
        self.exporter = next(x for x in self.crawler.extensions.middlewares if isinstance(x, FeedExporter))
        self.storage = self.exporter._get_storage(self.settings['FEED_URI'] % self.exporter._get_uri_params(self))
        self.marker_dir = self.settings['MARKER_DIR'] % self.exporter._get_uri_params(self)
        if not os.path.exists(self.marker_dir):
            os.makedirs(self.marker_dir)
        response = self.storage.s3_client.list_objects_v2(Bucket=self.storage.bucketname, Prefix=self.settings['MARKER'].split('.')[0])
        if 'Contents' in response:
            for content in response['Contents']:
                self.Marker = max(content['Key'], self.Marker)

    def upload_s3(self, keyname, fp):
        restore = self.storage.keyname
        self.storage.keyname = keyname
        # blocking or else synchro issue
        self.storage._store_in_thread(fp)
        self.storage.keyname = restore

    def download_s3(self, keyname, deserialize=pickle.loads):
        response = self.storage.s3_client.get_object(Bucket=self.storage.bucketname, Key=keyname)
        return deserialize(response['Body'].read())

    def closed(self, reason):
        return
