import asyncio
import psycopg
import pytest
import pytest_asyncio
from dual_choice.db import db


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    await db.init_pool()
    await db.init_db(clean=True)
    yield db.pool
    await db.pool.close()


@pytest.mark.asyncio
async def test_insert_selection(setup_database):
    pool = setup_database
    await db.insert_selection("user1", 1, 2, 3)
    await db.insert_selection("user2", 1, 2, 3)
    await db.insert_selection("user3", 1, 3, 2)

    # noise
    await db.insert_selection("user1", 1, 2, 4)
    await db.insert_selection("user1", 2, 2, 3)
    n_ins = 5

    # count rows
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select count(1) as cnt from image_selections")
            res = await cur.fetchone()
            assert int(res[0]) == n_ins

    # 66% 2-3
    result = await db.get_prop_selected(1, 2, 3)
    assert result[0] == 2
    assert result[1] == 3

    # 33% 3-2 (complement to the previous result)
    result = await db.get_prop_selected(1, 3, 2)
    assert result[0] == 1
    assert result[1] == 3

    # no such id, zero all
    result = await db.get_prop_selected(999, 2, 3)
    assert result[0] == 0
    assert result[1] == 0

    # error on duplicate insertion
    with pytest.raises(psycopg.errors.UniqueViolation):
        await db.insert_selection("user1", 1, 2, 3)

    new_ins = 100

    async def concurrent_inserts():
        tasks = [db.insert_selection(f"user{i}", 4, 1, 2) for i in range(new_ins)]
        await asyncio.gather(*tasks)

    await concurrent_inserts()

    # count rows
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select count(1) as cnt from image_selections")
            res = await cur.fetchone()
            assert int(res[0]) == n_ins + new_ins

    # simulate long concurrent queries to make sure it is really async


@pytest.mark.asyncio
async def test_insert_selection2(setup_database):
    pool = setup_database
    await db.insert_selection("user1", 1, 2, 3)
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select count(1) as cnt from image_selections")
            res = await cur.fetchone()
            print(res)
            assert int(res[0]) == 1


# @pytest.mark.asyncio
# async def test_get_prop_selected_empty():
#     result = await get_prop_selected(999, 999, 999)
#     assert result["selected_count"] == 0
#     assert result["total_count"] == 0
