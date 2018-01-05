from CraigSpider import CraigSpider

class DmozSpider(CraigSpider):
    name = "sfc"
    start_urls = [
         "http://sfbay.craigslist.org/search/sfc/apa?max_bedrooms=1",
         "http://sfbay.craigslist.org/search/sfc/sub?max_bedrooms=1",
    ]
