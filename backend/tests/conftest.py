from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..app.main import create_app
from ..app.models import Base, User, Tweet, Follow, Like
from ..app.database import get_session


TEST_DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5432/test_db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine, expire_on_commit=False, class_=AsyncSession
)

@pytest_asyncio.fixture
async def app(session):
    _app = create_app(TEST_DATABASE_URL)
    _app.dependency_overrides[get_session] = lambda: session
    yield _app
    _app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def _engine():
    async with test_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

@pytest_asyncio.fixture
async def session(_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as test_session:
        async with test_session.begin():
            yield test_session

@pytest_asyncio.fixture
async def app_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def seed_data(session):
    user_1 = User(name="user1")
    user_2 = User(name="user2")
    tweet = Tweet(tweet_data="Some text data", author_id=1)
    like = Like(user_id=2, tweet_id=1)
    follow = Follow(follower_id=2, followee_id=1)

    session.add_all([user_1, user_2, tweet, like, follow])
    await session.flush()






