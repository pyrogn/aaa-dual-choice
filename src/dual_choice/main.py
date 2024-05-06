"""AB testing image enhancements."""

# beauty:
# progress bar
# fix percentages
# add extra images for fun
# add ddos protection (use limits)

import json
import os
import random
from contextlib import asynccontextmanager
from itertools import combinations

import psycopg
import redis
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

redis_client = redis.Redis(host="redis", port=6379, db=0)
redis_client.flushdb()
DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL


def acquire_lock(user_id):
    return redis_client.set(
        f"lock:{user_id}", "true", nx=True, ex=10
    )  # 10 seconds expiration


def release_lock(user_id):
    redis_client.delete(f"lock:{user_id}")


# pairs should be in format list[pair] which is
# values of pairs should be paths to images
# user_id: [(image_id1, version1, version2), (image_id2, version3, version9)]


# I separate them because I can only pop after I wrote a user choice in DB
def get_user_pairs(user_id: str) -> list[tuple]:
    if redis_client.llen(user_id) == 0:
        return []
    return json.loads(redis_client.lindex(user_id, 0))


def rm_first_user_pair(user_id: str) -> None:
    print("removed:", redis_client.lpop(user_id))


def add_user_pairs(user_id: str, pairs: list[tuple]):
    redis_client.rpush(user_id, *[json.dumps(i) for i in pairs])


def get_db_connection():
    conn = psycopg.connect(DATABASE_URL)
    return conn


def execute_sql(query, params):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def init_db():
    # подумать, как лучше перезаписывать таблицу
    execute_sql(
        """
        drop table if exists image_selections
        """,
        [],
    )
    # добавить таймштамп (автоматический) ?
    execute_sql(
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


templates = Jinja2Templates(directory="src/dual_choice/templates")

data_directory = "data"

# Mount the 'data' directory as a static directory
app.mount("/data", StaticFiles(directory=data_directory), name="data")


def generate_image_pairs(data_directory: str) -> list[tuple]:
    """Generate image pairs based on data, ensuring no duplicates."""
    folders = [f.path for f in os.scandir(data_directory) if f.is_dir()]
    pairs = []
    random.shuffle(folders)

    for folder in folders:
        images = os.listdir(folder)
        combs = list(combinations(images, r=2))
        random.shuffle(combs)
        for comb in combs:
            pairs.append([folder, *comb])
    random.shuffle(pairs)
    print(pairs)
    return pairs


def get_image_for_user(user_id: str):
    if redis_client.llen(user_id) == 0:
        pairs = generate_image_pairs(data_directory)
        add_user_pairs(user_id, pairs)
    print("pair: ", get_user_pairs(user_id))
    return get_user_pairs(user_id)


def get_paths_from_pair(pair):
    """From image id|id1|id2 get paths of two images, adding random position"""
    folder, *lr_imgs = pair
    print("lr_images:", lr_imgs)

    random.shuffle(lr_imgs)
    imgs_with_paths = [os.path.join(folder, i) for i in lr_imgs]
    print("imgs with paths:", imgs_with_paths)
    return imgs_with_paths


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
