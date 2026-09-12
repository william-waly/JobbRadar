import json
import logging

from itemadapter import ItemAdapter

from app.queue.redis_client import get_redis_client

logger = logging.getLogger(__name__)

QUEUE_KEY = "jobs:queue"


class RedisQueuePipeline:
    """Sender hvert scraped item til Redis-køen i stedet for kun til fil."""

    def open_spider(self, spider):
        self.redis_client = get_redis_client()
        logger.info("Koblet til Redis for kø '%s'.", QUEUE_KEY)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        payload = json.dumps(adapter.asdict(), ensure_ascii=False)
        self.redis_client.rpush(QUEUE_KEY, payload)
        return item

    def close_spider(self, spider):
        queue_length = self.redis_client.llen(QUEUE_KEY)
        logger.info("Ferdig. %s jobber venter i køen.", queue_length)