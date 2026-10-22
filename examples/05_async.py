import asyncio
import time

from fastapi import FastAPI

app = FastAPI()
BAKE_SECONDS = 2


@app.get("/bake/async")
async def bake_async():
    await asyncio.sleep(BAKE_SECONDS)  # waiter serves other tables ✅
    return {"pizza": "ready"}


@app.get("/bake/blocking")
async def bake_blocking():
    time.sleep(BAKE_SECONDS)  # waiter freezes at the oven ❌
    return {"pizza": "ready"}


@app.get("/bake/threadpool")
def bake_threadpool():
    time.sleep(BAKE_SECONDS)  # `def` runs in a thread pool ✅
    return {"pizza": "ready"}
