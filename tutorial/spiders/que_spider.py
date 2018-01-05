from CraigSpider import CraigSpider

class QueSpider(CraigSpider):
    name = "queens"
    start_urls = [
        "https://newyork.craigslist.org/search/que/sub?min_bedrooms=0&max_bedrooms=1&private_room=1&private_bath=1",
    ]
