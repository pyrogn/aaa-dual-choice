import psycopg
import pytest
import pytest_asyncio
from dual_choice.db import get_prop_selected, init_db, insert_selection, init_async_pool


# solve the problem with closed loop (cannot create second pytest function)


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    pool = await init_async_pool()
    await init_db()
    yield pool
    # clean db here maybe


@pytest.mark.asyncio
async def test_insert_selection(setup_database):
    pool = setup_database
    await insert_selection("user1", 1, 2, 3)
    await insert_selection("user2", 1, 2, 3)
    await insert_selection("user3", 1, 3, 2)

    # noise
    await insert_selection("user1", 1, 2, 4)
    await insert_selection("user1", 2, 2, 3)

    # count rows
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select count(1) as cnt from image_selections")
            res = await cur.fetchone()
            assert int(res[0]) == 5

    # 66% 2-3
    result = await get_prop_selected(1, 2, 3)
    assert result[0] == 2
    assert result[1] == 3

    # 33% 3-2 (complement to the previous result)
    result = await get_prop_selected(1, 3, 2)
    assert result[0] == 1
    assert result[1] == 3

    # no such id, zero all
    result = await get_prop_selected(999, 2, 3)
    assert result[0] == 0
    assert result[1] == 0

    # error on duplicate insertion
    with pytest.raises(psycopg.errors.UniqueViolation):
        await insert_selection("user1", 1, 2, 3)


# @pytest.mark.asyncio
# async def test_insert_selection2(setup_database):
#     pool = setup_database
#     await insert_selection("user1", 1, 2, 3)
#     async with pool.connection() as conn:
#         async with conn.cursor() as cur:
#             await cur.execute("select count(1) as cnt from image_selections")
#             res = await cur.fetchone()
#             print(res)
#             assert int(res[0]) == 1


# @pytest.mark.asyncio
# async def test_get_prop_selected_empty():
#     result = await get_prop_selected(999, 999, 999)
#     assert result["selected_count"] == 0
#     assert result["total_count"] == 0
