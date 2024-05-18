import os
from typing import Any
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/database"
)
assert DATABASE_URL

# Initialize the connection pool
async_pool: AsyncConnectionPool


async def init_async_pool():
    global async_pool
    async_pool = AsyncConnectionPool(conninfo=DATABASE_URL, open=False)
    await async_pool.open()
    return async_pool


async def init_db():
    await execute_sql("""
        DROP TABLE IF EXISTS image_selections
    """)
    await execute_sql("""
        CREATE TABLE IF NOT EXISTS image_selections (
            user_id TEXT,
            image_id INTEGER,
            selected_id INTEGER,
            other_id INTEGER,
            timestamp timestamp default current_timestamp,
            PRIMARY KEY (user_id, image_id, selected_id, other_id)
        )
    """)


async def execute_sql(query: str, params: list[Any] | None = None):
    if params is None:
        params = []
    async with async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)
            await conn.commit()


async def insert_selection(
    user_id: str, image_id: int, selected_id: int, other_id: int
):
    await execute_sql(
        """
        INSERT INTO image_selections (user_id, image_id, selected_id, other_id)
        VALUES (%s, %s, %s, %s)
    """,
        [user_id, image_id, selected_id, other_id],
    )


async def get_prop_selected(
    image_id: int, selected_sub_id: int, non_selected_sub_id: int
):
    async with async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    COUNT(CASE WHEN selected_id = %s AND other_id = %s THEN 1 ELSE NULL END) AS selected_count,
                    COUNT(1) AS total_count
                FROM image_selections
                WHERE image_id = %s AND (
                    (selected_id = %s AND other_id = %s) OR
                    (selected_id = %s AND other_id = %s)
                )
            """,
                [
                    selected_sub_id,
                    non_selected_sub_id,
                    image_id,
                    selected_sub_id,
                    non_selected_sub_id,
                    non_selected_sub_id,
                    selected_sub_id,
                ],
            )
            result = await cur.fetchone()
            return result
