from BaseSpider import BaseSpider

class DmozSpider(BaseSpider):
    name = "dmoz"
    start_urls = [
        "https://newyork.craigslist.org/search/mnh/abo?min_bedrooms=0&max_bedrooms=3&min_price=1000&max_price=5000&private_room=1&private_bath=1&availabilityMode=0",
        "https://newyork.craigslist.org/search/mnh/sub?min_bedrooms=0&max_bedrooms=3&min_price=1000&max_price=5000&private_room=1&private_bath=1&availabilityMode=0",
    ]
