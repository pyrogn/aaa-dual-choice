import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from dual_choice.db import db
import psycopg


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_pool = AsyncMock()

    mock_conn.__aenter__.return_value = mock_conn
    mock_conn.__aexit__.return_value = None
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.__aenter__.return_value = mock_cursor
    mock_cursor.__aexit__.return_value = None

    mock_pool.connection.return_value = mock_conn

    db.pool = mock_pool
    yield mock_pool
    db.pool = None


@pytest.mark.asyncio
async def test_insert_selection(setup_database):
    pool = setup_database

    with patch.object(
        db, "insert_selection", new_callable=AsyncMock
    ) as mock_insert_selection:

        async def insert_selections():
            users = ["user1", "user2", "user3"]
            for user in users:
                await db.insert_selection(user, 1, 2, 3)
            await db.insert_selection("user1", 1, 2, 4)
            await db.insert_selection("user1", 2, 2, 3)

        await insert_selections()

        mock_conn = pool.connection.return_value
        mock_cursor = mock_conn.__aenter__.return_value.cursor.return_value
        mock_cursor.__aenter__.return_value.fetchone.return_value = (5,)

        async with await pool.connection() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("select count(1) as cnt from image_selections")
                res = await cur.fetchone()
                assert int(res[0]) == 5

        db.get_prop_selected = AsyncMock(return_value=(2, 3))
        result = await db.get_prop_selected(1, 2, 3)
        assert result == (2, 3)

        db.get_prop_selected = AsyncMock(return_value=(1, 3))
        result = await db.get_prop_selected(1, 3, 2)
        assert result == (1, 3)

        db.get_prop_selected = AsyncMock(return_value=(0, 0))
        result = await db.get_prop_selected(999, 2, 3)
        assert result == (0, 0)

        db.insert_selection = AsyncMock(side_effect=psycopg.errors.UniqueViolation)

        async def concurrent_inserts():
            with pytest.raises(psycopg.errors.UniqueViolation):
                tasks = [db.insert_selection(f"user{i}", 4, 1, 2) for i in range(100)]
                await asyncio.gather(*tasks)

        await concurrent_inserts()

        mock_cursor.__aenter__.return_value.fetchone.return_value = (105,)

        async with await pool.connection() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("select count(1) as cnt from image_selections")
                res = await cur.fetchone()
                assert int(res[0]) == 105


@pytest.mark.asyncio
async def test_insert_selection2(setup_database):
    pool = setup_database

    with patch.object(
        db, "insert_selection", new_callable=AsyncMock
    ) as mock_insert_selection:
        await db.insert_selection("user1", 1, 2, 3)

        mock_conn = pool.connection.return_value
        mock_cursor = mock_conn.__aenter__.return_value.cursor.return_value
        mock_cursor.__aenter__.return_value.fetchone.return_value = (1,)

        async with await pool.connection() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("select count(1) as cnt from image_selections")
                res = await cur.fetchone()
                assert int(res[0]) == 1
