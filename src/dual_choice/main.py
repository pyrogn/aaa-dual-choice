"""AB testing image enhancements."""

import json
import os
from contextlib import asynccontextmanager

import psycopg
from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from dual_choice.pairs_logic import generate_image_pairs, get_paths_from_pair

redis_client = redis.Redis(host="redis", port=6379, db=0)
redis_client.flushdb()
DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL


async def get_user_pairs(user_id: str) -> list[tuple]:
    if await redis_client.llen(user_id) == 0:
        return []
    return json.loads(await redis_client.lindex(user_id, 0))


async def rm_first_user_pair(user_id: str) -> None:
    print("removed:", await redis_client.lpop(user_id))


async def add_user_pairs(user_id: str, pairs: list[tuple]):
    await redis_client.rpush(user_id, *[json.dumps(i) for i in pairs])


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.async_pool = AsyncConnectionPool(conninfo=DATABASE_URL)  # type: ignore
    await init_db()
    yield
    await app.async_pool.close()  # type: ignore


async def execute_sql(query, params):
    # it is fastapi request, but how to use it?
    async with request.app.async_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, params)


async def init_db():
    # подумать, как лучше перезаписывать таблицу
    await execute_sql(
        """
        drop table if exists image_selections
        """,
        [],
    )
    # добавить таймштамп (автоматический) ?
    await execute_sql(
        """
        CREATE TABLE IF NOT EXISTS image_selections (
            user_id TEXT,
            image_id INTEGER,
            selected_id INTEGER,
            other_id INTEGER,
            PRIMARY KEY (user_id, image_id, selected_id, other_id)
            )
        """,
        [],
    )


app = FastAPI(lifespan=lifespan)


templates = Jinja2Templates(directory="src/dual_choice/templates")

data_directory = "data"

# Mount the 'data' directory as a static directory
app.mount("/data", StaticFiles(directory=data_directory), name="data")


def get_image_for_user(user_id: str):
    if redis_client.llen(user_id) == 0:
        pairs = generate_image_pairs(data_directory)
        add_user_pairs(user_id, pairs)
    print("pair: ", get_user_pairs(user_id))
    return get_user_pairs(user_id)


def get_user_id_from_request(request: Request) -> str:
    assert request.client
    user_id = f"{request.client.host}_{request.headers.get('User-Agent')}"
    return user_id


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_id = get_user_id_from_request(request)
    pairs = get_image_for_user(user_id)

    pair = get_paths_from_pair(pairs)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "images": [pair[0], pair[1]]},
    )


class ImageSelection(BaseModel):
    imageId: int
    selectedSubId: int
    nonSelectedSubId: int


@app.post("/")
async def save_selection(request: Request, selection: ImageSelection):
    user_id = get_user_id_from_request(request)
    try:
        execute_sql(
            """
            INSERT INTO image_selections (user_id, image_id, selected_id, other_id)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                selection.imageId,
                selection.selectedSubId,
                selection.nonSelectedSubId,
            ),
        )
        print(
            "inserted: ",
            (
                user_id,
                selection.imageId,
                selection.selectedSubId,
                selection.nonSelectedSubId,
            ),
        )
        # Remove the first pair from the user's queue
        rm_first_user_pair(user_id)
    except psycopg.errors.UniqueViolation:
        print("duplicate request")
        return {"message": "Duplicate request"}
    return {"message": "Selection saved"}


@app.get("/new-images")
async def get_new_images(request: Request):
    user_id = get_user_id_from_request(request)
    pairs = get_user_pairs(user_id)
    pair = get_paths_from_pair(pairs)
    print(pair)
    return {"images": [pair[0], pair[1]]}


@app.get("/selections/{image_id}/{selected_sub_id}/{non_selected_sub_id}")
async def get_selection_count(
    image_id: int, selected_sub_id: int, non_selected_sub_id: int
):
    conn = get_db_connection()
    cursor = conn.cursor()
    # might want to simplify this?
    cursor.execute(
        """
        SELECT
            SUM(CASE WHEN selected_id = ? AND other_id = ? THEN 1 ELSE 0 END)
                AS selected_count,
            COUNT(1) AS total_count
        FROM image_selections
        WHERE image_id = ? AND (
            (selected_id = ? AND other_id = ?) OR
            (selected_id = ? AND other_id = ?)
        )
    """,
        (
            selected_sub_id,
            non_selected_sub_id,
            image_id,
            selected_sub_id,
            non_selected_sub_id,
            non_selected_sub_id,
            selected_sub_id,
        ),
    )
    row = cursor.fetchone()
    if row:
        prop_selected = row["selected_count"] / row["total_count"]  # type: ignore
    else:
        prop_selected = 0
    conn.close()
    return {"prop_selected": prop_selected}
