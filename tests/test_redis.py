"""Testing redis functions."""

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from dual_choice.pairs_logic import generate_image_pairs
from setup_dir import setup_test_directory  # noqa: F401
from dual_choice.redis_logic import UserMemoryManagement


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_redis():
    redis_client = FakeRedis()
    await redis_client.flushdb()
    yield redis_client
    await redis_client.flushdb()
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_add_and_get_user_pairs(setup_test_directory, setup_redis):
    user_id = "test_user"
    pairs = generate_image_pairs(str(setup_test_directory))
    user_memory = UserMemoryManagement(setup_redis)

    await user_memory.add_user_pairs(user_id, pairs)
    first_pair = await user_memory.get_user_first_pair(user_id)
    await user_memory.rm_first_user_pair(user_id)

    assert len(first_pair) == 3
    assert first_pair == pairs[0]

    second_pair = await user_memory.get_user_first_pair(user_id)

    assert len(second_pair) == 3
    assert second_pair == pairs[1]
    await user_memory.rm_first_user_pair(user_id)

    # testing that we can exhaust full queue
    cnt_pairs = 2
    while (resp := await user_memory.get_user_first_pair(user_id)) is not None:
        cnt_pairs += 1
        await user_memory.rm_first_user_pair(user_id)
    assert len(pairs) == cnt_pairs
