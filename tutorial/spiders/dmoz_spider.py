from BaseSpider import BaseSpider

class DmozSpider(BaseSpider):
    name = "dmoz"
    start_urls = [
"https://newyork.craigslist.org/search/mnh/abo?nh=120&nh=134&nh=160&nh=121&nh=129&nh=122&nh=133&nh=132&nh=127&nh=126&nh=135&nh=136&nh=137&nh=131&nh=125&nh=124&nh=123&nh=130&nh=139&nh=138&nh=128&min_price=2800&max_price=3700&min_bedrooms=2&max_bedrooms=3&availabilityMode=1",
"https://newyork.craigslist.org/search/mnh/sub?nh=120&nh=134&nh=160&nh=121&nh=129&nh=122&nh=133&nh=132&nh=127&nh=126&nh=135&nh=136&nh=137&nh=131&nh=125&nh=124&nh=123&nh=130&nh=139&nh=138&nh=128&min_price=2800&max_price=3700&min_bedrooms=2&max_bedrooms=3&availabilityMode=1",
    ]
