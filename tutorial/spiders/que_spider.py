from BaseSpider import BaseSpider

class QueSpider(BaseSpider):
    name = "que"
    start_urls = [
        "https://newyork.craigslist.org/search/que/sub?min_bedrooms=0&max_bedrooms=3&private_room=1&private_bath=1",
    ]
