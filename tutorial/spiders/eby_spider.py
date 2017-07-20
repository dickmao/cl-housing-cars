from BaseSpider import BaseSpider

class DmozSpider(BaseSpider):
    name = "eby"
    start_urls = [
"https://sfbay.craigslist.org/search/eby/apa?min_bedrooms=2&min_bathrooms=2&availabilityMode=0",
    ]
