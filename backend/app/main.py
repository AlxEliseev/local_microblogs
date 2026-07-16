from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from logging import config as log_config
from .database import engine
from .exceptions import ApplicationException
from .routers import users, tweets, medias
from .logger_config import dict_config

log_config.dictConfig(dict_config)


def create_app():
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        await engine.dispose()

    _app = FastAPI(lifespan=lifespan)

    @_app.exception_handler(ApplicationException)
    async def custom_exception_handler(request, exc: ApplicationException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "result": False,
                "error_type": exc.error_type,
                "error_message": exc.detail,
            },
        )

    _app.include_router(users.router)
    _app.include_router(tweets.router)
    _app.include_router(medias.router)

    return _app


app = create_app()
