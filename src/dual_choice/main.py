from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from psycopg.errors import UniqueViolation

from dual_choice.db import db
from dual_choice.pairs_logic import generate_image_pairs, get_image_paths
from dual_choice.redis_logic import (
    get_user_first_pair,
    rm_first_user_pair,
    add_user_pairs,
    redis_client,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await db.init_db(clean=True)
    await redis_client.flushall(asynchronous=True)
    yield
    await db.pool.close()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="src/dual_choice/templates")

data_directory = "data"

# Mount the 'data' directory as a static directory
app.mount("/data", StaticFiles(directory=data_directory), name="data")


def get_user_id_from_request(request: Request) -> str:
    assert request.client
    user_id = (
        f"{request.client.host}_{request.headers.get('User-Agent', 'no user agent')}"
    )
    return user_id


async def get_image_for_user(user_id: str):
    if await redis_client.llen(user_id) == 0:
        # # print that you are very good, thank you
        # raise HTTPException(status_code=404, detail="Game is over!!!")

        # do something with database (because we won't be able to insert new rows)
        pairs = generate_image_pairs(data_directory)
        await add_user_pairs(user_id, pairs)
    return await get_user_first_pair(user_id)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render a main page for a user."""
    user_id = get_user_id_from_request(request)
    pair = await get_image_for_user(user_id)

    if pair is None:
        raise HTTPException(status_code=404, detail="No image pairs available")

    image_paths = get_image_paths(pair)
    return templates.TemplateResponse(
        "index.html", {"request": request, "images": image_paths, "user_id": user_id}
    )


class ImageSelection(BaseModel):
    imageId: int
    selectedSubId: int
    nonSelectedSubId: int


@app.post("/")
async def save_selection(request: Request, selection: ImageSelection):
    """Process a user's choice."""
    user_id = get_user_id_from_request(request)
    lock_key = f"{user_id}_lock"

    if await redis_client.setnx(lock_key, "locked"):
        try:
            # check how many users selected also, not great to do it inside a lock
            # I can make it as a new key in redis for user and set in get request
            count = await get_selection_count(
                selection.imageId, selection.selectedSubId, selection.nonSelectedSubId
            )
            await redis_client.expire(lock_key, 5)  # Set expiration time for the lock
            await db.insert_selection(
                user_id,
                selection.imageId,
                selection.selectedSubId,
                selection.nonSelectedSubId,
            )
            await rm_first_user_pair(user_id)
        except UniqueViolation:
            raise HTTPException(status_code=400, detail="Duplicate request")
        finally:
            await redis_client.delete(lock_key)
    else:
        raise HTTPException(status_code=400, detail="Duplicate request")

    return {"message": "Selection saved", "count": count}


@app.get("/new-images")
async def get_new_images(request: Request):
    # not used for now
    user_id = get_user_id_from_request(request)
    pair = await get_image_for_user(user_id)

    if pair is None:
        raise HTTPException(status_code=404, detail="No image pairs available")

    image_paths = get_image_paths(pair)
    return {"images": image_paths}


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
