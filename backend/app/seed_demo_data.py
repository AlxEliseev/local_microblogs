from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
import asyncio
import factory
import random


from .models import Base, User, Tweet, Follow, Like
from .config import DATABASE_URL

# for local running script uncomment
# DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5432/twitter_db"

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)
session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class UserFactory(factory.Factory):
    class Meta:
        model = User

    name = factory.Faker("name")


class TweetFactory(factory.Factory):
    class Meta:
        model = Tweet

    tweet_data = factory.Faker("text", max_nb_chars=200)

    author = None


async def seed_demo_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:

        async with session.begin():
            print("Генерация пользователей...")

            users = [UserFactory.build() for _ in range(10)]
            session.add_all(users)
            await session.flush()

            print("Генерация твитов...")
            tweets = []
            for user in users:
                for _ in range(random.randint(1, 5)):
                    tweet = TweetFactory.build(author=user)
                    tweets.append(tweet)
            session.add_all(tweets)
            await session.flush()

            print("Генерация подписок и лайков...")

            relations = []

            for current_user in users:

                num_follows = random.randint(2, min(5, len(users) - 1))

                possible_foes = [u for u in users if u.id != current_user.id]
                tracked_users = random.sample(possible_foes, num_follows)

                for target_user in tracked_users:
                    follow = Follow(
                        follower_id=current_user.id, followee_id=target_user.id
                    )
                    relations.append(follow)

            for current_user in users:
                num_likes = random.randint(3, min(7, len(tweets)))
                liked_tweets = random.sample(tweets, num_likes)

                for tweet in liked_tweets:
                    like = Like(user_id=current_user.id, tweet_id=tweet.id)
                    relations.append(like)

            session.add_all(relations)

        print("База данных успешно заполнена демо-данными!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
