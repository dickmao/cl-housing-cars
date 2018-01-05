from .CraigSpider import CraigSpider

class ToySpider(CraigSpider):
    name = "toy"
    start_urls = [
        "https://newyork.craigslist.org/search/cto?query=prius&search_distance=50&postal=11747&max_price=10000",
    ]
