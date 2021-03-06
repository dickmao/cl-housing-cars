from .CraigSpider import CraigSpider

class BoroughsSpider(CraigSpider):
    name = "boroughs"
    start_urls = [
        "https://newyork.craigslist.org/search/brk/abo?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://newyork.craigslist.org/search/brk/sub?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://newyork.craigslist.org/search/brx/sub?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://newyork.craigslist.org/search/brx/abo?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://newyork.craigslist.org/search/stn/sub?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://newyork.craigslist.org/search/stn/abo?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
    ]
