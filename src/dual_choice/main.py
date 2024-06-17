from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from psycopg.errors import UniqueViolation
import redis.asyncio as redis
import os

from dual_choice.db import Database
from dual_choice.pairs_logic import (
    generate_image_pairs,
    get_image_paths,
    count_image_pairs,
)
from dual_choice.redis_logic import UserMemoryManagement

load_dotenv()
redis_url = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_url)

user_memory = UserMemoryManagement(redis_client=redis_client)
DATABASE_URL = os.getenv("DATABASE_URL")
db = Database(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await db.init_db(clean=False)
    yield
    await db.pool.close()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="src/dual_choice/templates")

data_directory = "data-min"  # folder with versions of images

app.mount(f"/{data_directory}", StaticFiles(directory=data_directory), name="data")


def get_user_id_from_request(request: Request) -> str:
    """UserID = IP + UserAgent."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip = forwarded_for.split(",")[0] if forwarded_for else request.client.host
    user_id = f"{ip}_{request.headers.get('User-Agent', 'no user agent')}"
    return user_id


async def get_image_for_user(user_id: str):
    """Get pair of images for user and get None if he's completed the survey."""
    if await user_memory.is_new_user(user_id):
        pairs = generate_image_pairs(data_directory)
        await user_memory.add_user_pairs(user_id, pairs)
        await user_memory.mark_user_initialized(user_id)

    max_num_pairs = await user_memory.get_max_num_pairs()
    if max_num_pairs == 0:
        total_pairs = count_image_pairs(data_directory)
        await user_memory.set_max_num_pairs(total_pairs)

    return await user_memory.get_user_first_pair(user_id)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_id = get_user_id_from_request(request)
    pair = await get_image_for_user(user_id)

    if pair is None:
        return templates.TemplateResponse("thank_you.html", {"request": request})

    image_paths = get_image_paths(pair)
    n_pairs = await user_memory.get_user_num_pairs(user_id)
    tot_pairs = await user_memory.get_max_num_pairs()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "images": image_paths,
            "user_id": user_id,
            "cur_progress": tot_pairs - n_pairs,
            "tot_progress": tot_pairs,
        },
    )


class ImageSelection(BaseModel):
    imageId: int
    selectedSubId: int
    nonSelectedSubId: int


@app.post("/")
async def save_selection(request: Request, selection: ImageSelection):
    user_id = get_user_id_from_request(request)
    lock_key = f"{user_id}_lock"

    if await user_memory.acquire_lock(lock_key):
        try:
            count = await get_selection_count(
                selection.imageId, selection.selectedSubId, selection.nonSelectedSubId
            )
            await db.insert_selection(
                user_id,
                selection.imageId,
                selection.selectedSubId,
                selection.nonSelectedSubId,
            )
            await user_memory.rm_first_user_pair(user_id)
        except UniqueViolation:
            await user_memory.release_lock(lock_key)
            raise HTTPException(status_code=400, detail="Duplicate request")
        finally:
            await user_memory.release_lock(lock_key)
    else:
        raise HTTPException(status_code=400, detail="Duplicate request")

    return {"message": "Selection saved", "count": count}


@app.get("/new-images")
async def get_new_images(request: Request):
    user_id = get_user_id_from_request(request)
    pair = await get_image_for_user(user_id)

    if pair is None:
        return {"images": []}

    image_paths = get_image_paths(pair)
    return {"images": image_paths}


@app.get("/progress")
async def get_progress(request: Request):
    user_id = get_user_id_from_request(request)
    cur_progress = await user_memory.get_user_num_pairs(user_id)
    tot_progress = await user_memory.get_max_num_pairs()
    return {"cur_progress": tot_progress - cur_progress, "tot_progress": tot_progress}


async def get_selection_count(
    image_id: int, selected_sub_id: int, non_selected_sub_id: int
):
    result = await db.get_prop_selected(image_id, selected_sub_id, non_selected_sub_id)
    if result:
        selected_count, total_count = result
        if total_count == 0:
            return None
        prop_selected = selected_count / total_count if total_count > 0 else 0
    else:
        prop_selected = 0

    return prop_selected
