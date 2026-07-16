from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..app.main import create_app
from ..app.models import Base, User, Tweet, Follow, Like, Media
from ..app.database import get_session

TEST_DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5432/test_db"


@pytest_asyncio.fixture
async def db_resources():
    """Создаёт engine и session_maker для каждого теста
    При попытке создания единого engine для всей тестовой сессии (scope='session')
    возникает ошибка:
     InterfaceError: cannot perform operation: another operation is in progress
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_maker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine, session_maker

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_resources) -> AsyncGenerator[AsyncSession, None]:
    """Выдает сессию для теста"""
    _, session_maker = db_resources
    async with session_maker() as test_session:
        yield test_session


@pytest_asyncio.fixture
async def app(db_resources):
    """Собирает приложение с переопределенной зависимостью"""
    _, session_maker = db_resources

    async def override_get_session():
        async with session_maker() as test_session:
            yield test_session

    _app = create_app()
    _app.dependency_overrides[get_session] = override_get_session
    yield _app

    _app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def app_client(app):
    """Клиент для выполнения HTTP-запросов"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def seed_data(session):
    """Заполнение базы данных тестовыми данными"""
    users = [User(name="user1"), User(name="user2")]

    session.add_all(users)
    await session.flush()

    tweet = Tweet(tweet_data="Some text data", author_id=users[0].id)
    media = Media(
        uuid="f18d1520-0c80-46af-b4ad-366027e6ad1a",
        mime_type="image/jpeg",
        size=100,
        relative_path="relative_path",
        tweet_id=1,
    )
    session.add_all([tweet, media])
    await session.flush()

    like = Like(user_id=users[1].id, tweet_id=tweet.id)
    follow = Follow(follower_id=users[1].id, followee_id=users[0].id)
    session.add_all([like, follow])

    await session.commit()
