import os
from dotenv import load_dotenv
import redis.asyncio as redis
import json

load_dotenv()
# for real app it should be host=redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)


async def get_user_first_pair(user_id: str) -> tuple[str, str, str] | None:
    if await redis_client.llen(user_id) == 0:
        return None
    return tuple(json.loads(await redis_client.lindex(user_id, 0)))


async def rm_first_user_pair(user_id: str) -> None:
    rm_user_id = await redis_client.lpop(user_id)
    # print("removed:", rm_user_id)


async def add_user_pairs(user_id: str, pairs: list[tuple]) -> None:
    await redis_client.rpush(user_id, *[json.dumps(i) for i in pairs])
