import os
from dotenv import load_dotenv
import redis.asyncio as redis
import json

load_dotenv()
# for real app it should be host=redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)


class UserMemoryManagement:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def get_user_first_pair(self, user_id: str) -> tuple[str, str, str] | None:
        if await self.redis_client.llen(user_id) == 0:
            return None
        return tuple(json.loads(await self.redis_client.lindex(user_id, 0)))

    async def rm_first_user_pair(self, user_id: str) -> None:
        rm_user_id = await self.redis_client.lpop(user_id)
        # print("removed:", rm_user_id)

    async def add_user_pairs(self, user_id: str, pairs: list[tuple]) -> None:
        await self.redis_client.rpush(user_id, *[json.dumps(i) for i in pairs])
