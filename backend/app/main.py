import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse

from . import models
from . import database
from .routers import users, tweets, medias

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:admin@postgres:5432/twitter_db"
)

def create_app(db_url: str):
    database.init_db(db_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # before app starts
        async with database.engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all, checkfirst=True)
        yield
        # after app finishes
        await database.close_db()

    _app = FastAPI(lifespan=lifespan)

    @_app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "result": False,
                "message": exc.detail
            }
        )

    _app.include_router(users.router)
    _app.include_router(tweets.router)
    _app.include_router(medias.router)

    return _app


app = create_app(DATABASE_URL)

