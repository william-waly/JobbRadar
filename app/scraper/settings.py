BOT_NAME = "jobbradar"

SPIDER_MODULES = ["app.scraper.spiders"]
NEWSPIDER_MODULE = "app.scraper.spiders"

# Vi konsumerer et offentlig, dokumentert API under NAVs vilkår for bruk,
# ikke en nettside vi crawler - robots.txt er derfor ikke relevant her.
ROBOTSTXT_OBEY = False

USER_AGENT = "JobbRadar (portfolio-prosjekt, ikke-kommersiell bruk)"

# Vær en god "netizen": ikke hamre løs på NAV sitt API.
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 2

LOG_LEVEL = "INFO"
FEED_EXPORT_ENCODING = "utf-8"