from typing import Any
from psycopg_pool import AsyncConnectionPool


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: AsyncConnectionPool | None = None

    async def init_pool(self):
        self.pool = AsyncConnectionPool(conninfo=self.database_url, open=False)
        await self.pool.open()
        return self.pool

    async def execute_sql(self, query: str, params: list[Any] | None = None):
        if params is None:
            params = []
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()

    async def init_db(self, clean=False):
        if clean:
            await self.execute_sql("""
                DROP TABLE IF EXISTS image_selections
            """)
        await self.execute_sql("""
            CREATE TABLE IF NOT EXISTS image_selections (
                user_id TEXT,
                image_id INTEGER,
                selected_id INTEGER,
                other_id INTEGER,
                timestamp timestamp default current_timestamp,
                PRIMARY KEY (user_id, image_id, selected_id, other_id)
            )
        """)

    async def insert_selection(
        self, user_id: str, image_id: int, selected_id: int, other_id: int
    ):
        await self.execute_sql(
            """
            INSERT INTO image_selections (user_id, image_id, selected_id, other_id)
            VALUES (%s, %s, %s, %s)
            """,
            [user_id, image_id, selected_id, other_id],
        )

    async def get_prop_selected(
        self, image_id: int, selected_sub_id: int, non_selected_sub_id: int
    ):
        async with self.pool.connection() as conn:
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
