from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse

from . import models
from .database import engine, init_db, close_db
from .routers import users, tweets, medias


def create_app(db_url: str):
    init_db(db_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # before app starts
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        yield
        # after app finishes
        await close_db()

    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "result": False,
                "message": exc.detail
            }
        )

    app.include_router(users.router)
    app.include_router(tweets.router)
    app.include_router(medias.router)

    return app


if __name__ == "__main__":
    app = create_app()

