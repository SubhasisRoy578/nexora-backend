from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
REDIS_URL = os.getenv("REDIS_URL")

mongo_client = None
db = None
redis_client = None


async def init_db():
    global mongo_client, db, redis_client

    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client["nexora_ai"]

    redis_client = redis.from_url(REDIS_URL)


async def close_db():
    global mongo_client, redis_client

    if mongo_client:
        mongo_client.close()

    if redis_client:
        await redis_client.close()


def get_database():
    return db


def get_redis():
    return redis_client