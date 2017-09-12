from BaseSpider import BaseSpider

class DmozSpider(BaseSpider):
    name = "que"
    start_urls = [
        "https://newyork.craigslist.org/search/que/sub?min_bedrooms=1&max_bedrooms=2&private_room=1&private_bath=1",
    ]
