import json
import redis.asyncio


class UserMemoryManagement:
    def __init__(self, redis_client: redis.asyncio.Redis):
        self.redis_client: redis.asyncio.Redis = redis_client
        self.max_num_pairs: int = 0

    async def get_user_first_pair(self, user_id: str) -> tuple[str, str, str] | None:
        if await self.redis_client.llen(user_id) == 0:
            return None
        return tuple(json.loads(await self.redis_client.lindex(user_id, 0)))

    async def rm_first_user_pair(self, user_id: str) -> None:
        await self.redis_client.lpop(user_id)

    async def add_user_pairs(self, user_id: str, pairs: list[tuple]) -> None:
        await self.redis_client.rpush(user_id, *[json.dumps(i) for i in pairs])

    async def get_user_num_pairs(self, user_id: str) -> int | None:
        resp = await self.redis_client.llen(user_id)
        return int(resp) if resp else 0

    async def set_max_num_pairs(self, set_num_pairs: int) -> None:
        await self.redis_client.set("max_pairs", set_num_pairs)
        self.max_num_pairs = set_num_pairs

    async def get_max_num_pairs(self) -> int:
        if self.max_num_pairs == 0:
            max_pairs = await self.redis_client.get("max_pairs")
            if max_pairs:
                self.max_num_pairs = int(max_pairs)
        return self.max_num_pairs

    async def acquire_lock(self, lock_key: str) -> bool:
        return await self.redis_client.setnx(lock_key, "locked")

    async def release_lock(self, lock_key: str) -> None:
        await self.redis_client.delete(lock_key)

    async def is_new_user(self, user_id: str) -> bool:
        return not await self.redis_client.exists(f"{user_id}_initialized")

    async def mark_user_initialized(self, user_id: str) -> None:
        await self.redis_client.set(f"{user_id}_initialized", "true")
