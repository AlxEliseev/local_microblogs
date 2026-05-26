from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker, create_async_engine


DATABASE_URL = "postgresql+asyncpg:///./twitter_clone.db"

engine: AsyncEngine | None = None
session_maker: async_sessionmaker[AsyncSession] | None = None


def init_db(db_url=DATABASE_URL):
    global engine, session_maker
    engine = create_async_engine(db_url, echo=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session

async def close_db() -> None:
    if engine is not None:
        await engine.dispose()


