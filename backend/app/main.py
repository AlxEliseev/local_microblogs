from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .database import engine
from .exceptions import ApplicationException
from .routers import users, tweets, medias
from .logger_config import setup_logging

setup_logging()

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
                "error_message": exc.detail
            }
        )

    _app.include_router(users.router)
    _app.include_router(tweets.router)
    _app.include_router(medias.router)

    return _app

app = create_app()

