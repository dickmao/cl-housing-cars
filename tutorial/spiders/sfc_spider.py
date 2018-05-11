from .CraigSpider import CraigSpider

class sfbaySpider(CraigSpider):
    name = "sfbay"
    start_urls = [
        "https://sfbay.craigslist.org/search/sfc/apa?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://sfbay.craigslist.org/search/sfc/sub?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://sfbay.craigslist.org/search/eby/apa?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
        "https://sfbay.craigslist.org/search/eby/sub?min_bedrooms=0&max_bedrooms=3&min_price=500&max_price=5000&private_room=1&private_bath=1",
    ]
