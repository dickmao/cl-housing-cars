from BaseSpider import BaseSpider

class DmozSpider(BaseSpider):
    name = "que"
    start_urls = [
        "https://newyork.craigslist.org/search/que/sub?min_bedrooms=1&max_bedrooms=1&min_bathrooms=1&max_bathrooms=1&availabilityMode=0&private_room=1&private_bath=1",
    ]
