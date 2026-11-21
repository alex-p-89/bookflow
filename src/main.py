import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError

from src.config import settings
from src.routers import auth_router, books_router, bookshelf_router, users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASS,
        socket_connect_timeout=2.0,
        socket_timeout=2.0,
        retry=Retry(NoBackoff(), 0),
        decode_responses=True,
    )
    app.state.redis = redis_client

    try:
        await asyncio.wait_for(redis_client.ping(), timeout=3.0)
        print("\nRedis online")
        redis_online = True
    except (RedisError, asyncio.TimeoutError, OSError) as e:
        print(f"\nRedis offline ({type(e).__name__}): {e}")
        redis_online = False

    app.state.redis_online = redis_online
    yield

    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)
app.include_router(books_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(bookshelf_router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
