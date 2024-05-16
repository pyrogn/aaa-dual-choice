"""Testing redis functions."""

import pytest
import pytest_asyncio
import redis.asyncio as redis
from dual_choice.pairs_logic import generate_image_pairs
from setup_dir import setup_test_directory  # noqa: F401
from dual_choice.redis_logic import (
    get_user_first_pair,
    add_user_pairs,
    rm_first_user_pair,
)


# for some reason I cannot reuse event loop in a second function
# don't like hardcode redis url
@pytest_asyncio.fixture(scope="function")
async def setup_redis():
    redis_url = "redis://localhost:6379/0"
    redis_client = redis.from_url(redis_url)
    await redis_client.flushdb()
    yield redis_client
    await redis_client.flushdb()
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_add_and_get_user_pairs(setup_redis, setup_test_directory):
    redis_client = setup_redis
    user_id = "test_user"
    pairs = generate_image_pairs(str(setup_test_directory))

    await add_user_pairs(user_id, pairs)
    first_pair = await get_user_first_pair(user_id)
    await rm_first_user_pair(user_id)

    assert len(first_pair) == 3
    assert first_pair == pairs[0]

    second_pair = await get_user_first_pair(user_id)

    assert len(second_pair) == 3
    assert second_pair == pairs[1]
    await rm_first_user_pair(user_id)

    # testing that we can exhaust full queue
    cnt_pairs = 2
    while (resp := await get_user_first_pair(user_id)) is not None:
        cnt_pairs += 1
        await rm_first_user_pair(user_id)
    assert len(pairs) == cnt_pairs
