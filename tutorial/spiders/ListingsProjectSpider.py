from tutorial.items import ListingsProjectItem
from datetime import date, timedelta, datetime
from .BaseSpider import BaseSpider
from git import Repo
import editdistance
import json, pickle, dateutil, shutil, errno, pytz, os
from collections import defaultdict
import tempfile, subprocess

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
        self.wednesdays = [self._wednesday((datetime.now(pytz.timezone("US/Eastern")) - timedelta(days=7*i, seconds=3600*10)).date())
                           for i in range(4)]
        try:
            shutil.rmtree('/var/tmp/.play-app')
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        password = os.environ.get('GIT_PASSWORD')
        if not password:
            with tempfile.NamedTemporaryFile() as temp:
                temp.write("protocol=https\nhost=github.com\n")
                temp.seek(0)
                output = { lst[0]: lst[1] for lst in [line.split("=") for line in subprocess.check_output(['git', 'credential', 'fill'], stdin=temp).rstrip().split("\n")]}
                password = output['password']
        play_app = Repo.clone_from("https://{}@github.com/dickmao/play-app.git".format(password), 
                                   to_path='/var/tmp/.play-app', 
                                   **{"depth": 1, "single-branch": True, "no-checkout": True})
        play_app.git.checkout('HEAD', "conf/NY.P.tsv")
        self._alphabins = defaultdict(lambda: dict())
        with open("/var/tmp/.play-app/conf/NY.P.tsv", 'r') as fp:
            for line in fp:
                arr = line.rstrip('\n').split('\t')
                self._alphabins[arr[2][0].lower()][arr[2]] = (arr[4], arr[5])

    def _set_crawler(self, crawler):
        super(ListingsProjectSpider, self)._set_crawler(crawler)
        old_wednesdays = self.download_s3(self.Marker) if self.Marker else []
        for w in self.wednesdays:
            if w not in old_wednesdays:
                self.start_urls.append("https://www.listingsproject.com/newsletter/{}/new-york-city".format(w))

    def closed(self, reason):
        super(ListingsProjectSpider, self).closed(reason)
        if self.exporter.slot.itemcount:
            marker = self.settings['MARKER'] % self.exporter._get_uri_params(self)

            file = self.storage.open(self)
            pickle.dump(self.wednesdays, file)
            self.upload_s3(marker, file)

            with open(os.path.join(self.marker_dir, marker), 'w+') as fp:
                pickle.dump(self.wednesdays, fp)


    def _guess_place(self, x):
        try:
            result = min(self._alphabins[x[0].lower()].items(),
                         key=lambda p: editdistance.eval(x, p[0]))
        except ValueError:
            result = (None, (None, None))
        return result

    def parse(self, response):
        item = ListingsProjectItem()
        blob = json.loads(response.xpath('//div/@data-react-props').extract_first())
        for listing in blob['initialListings']:
            if listing['subcategory_key'] in set(['apt_sublet', 'apt_rent', 'lease_takeover', 'room_rent', 'room_sublet']):
                # I don't use listing.get('about_you', '') because the entry always exists and its value is often None
                item['desc'] = listing['description'] + '\n' + (listing.get('about_you') or "")
                item['link'] = response.urljoin("listing/{}".format(listing['slug']))
                item['title'] = listing['headline']
                item['id'] = str(listing['id'])
                item['listedby'] = listing['name']
                item['coords'] = self._guess_place(listing['geo_neighborhood'])[1]
                item['posted'] = pytz.timezone('US/Eastern').localize(dateutil.parser.parse(listing['newsletter']['email_date'])).replace(hour=8).isoformat()
                item['updated'] = item['posted']
                item['price'] = listing['price']

                if item['desc']:
                    yield item
