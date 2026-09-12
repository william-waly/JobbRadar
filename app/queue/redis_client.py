import os

import redis
from dotenv import load_dotenv

load_dotenv()


def get_redis_client() -> redis.Redis:
    """Oppretter en Redis-klient basert på miljøvariabler."""
    return redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        decode_responses=True,
    )