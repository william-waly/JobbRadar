import scrapy


class JobItem(scrapy.Item):
    external_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()
    url = scrapy.Field()
    published_at = scrapy.Field()
    source_name = scrapy.Field()