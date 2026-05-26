import pytest
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError

from ..app.models import User, Tweet, Follow, Media, Like

# Проверка User:
@pytest.mark.asyncio
async def test_create_user(seed_data, session):
    """Создание нового пользователя"""
    stmt = select(User)
    rv = await session.execute(stmt)
    users = rv.all()
    users_start_count = len(users)

    user: User = User(name="new_user")
    session.add(user)
    await session.flush()

    rv = await session.execute(stmt)
    users = rv.all()
    assert len(users) == users_start_count + 1

@pytest.mark.asyncio
async def test_create_user_wo_name_exception(seed_data, session):
    """Нельзя создать пользователя без имени"""
    user: User = User()
    session.add(user)
    with pytest.raises(IntegrityError):
        await session.flush()

# Проверка Follow:

@pytest.mark.asyncio
async def test_wrong_followee_exception(seed_data, session):
    """Попытка создать Follow с несуществующим followee должна упасть"""
    follow: Follow = Follow(follower_id=1, followee_id=5)
    session.add(follow)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_append_followed_creates_follow(seed_data, session):
    """
    Добавление через association_proxy: user.followed.append(other)
    должно создавать Follow (проверка creator)
    """
    user_1: User | None = await session.get(User, 1)
    user_2: User | None = await session.get(User, 2)
    assert user_1
    assert user_2

    user_1.followed.append(user_2) # type: ignore
    await session.flush()

    stmt = select(Follow).where(Follow.followee_id == 2)
    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow.id == 2
    assert follow.follower_id == 1
    assert follow.followee_id == 2

    assert user_2.followers[0].id == 1

@pytest.mark.asyncio
async def test_double_follow_exception(seed_data, session):
    """Попытка создать дубликат follow должна упасть (проверить уникальный индекс)."""
    follow = Follow(follower_id=2, followee_id=1)
    session.add(follow)
    with pytest.raises(IntegrityError):
        await session.flush()

@pytest.mark.asyncio
async def test_self_follow_exception(seed_data, session):
    """Попытка self‑follow должна упасть (проверить CHECK)."""
    follow = Follow(follower_id=1, followee_id=1)
    session.add(follow)
    with pytest.raises(IntegrityError):
        await session.flush()

@pytest.mark.asyncio
async def test_delete_user_no_orphans_left(seed_data, session):
    """
    Удаление user через session.delete(user) должно удалять связанные Follow‑записи
    (и не оставлять орфанов).
    """
    user_1: User | None = await session.get(User, 1)
    user_2: User | None = await session.get(User, 2)
    assert user_1
    assert user_1.name == "user1"
    assert user_2.followed[0].id == 1

    stmt = select(Follow).where(Follow.followee_id == 1)
    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow.id == 1
    assert follow.follower_id == 2
    assert follow.followee_id == 1
    await session.delete(user_1)
    await session.flush()

    rv = await session.execute(stmt)
    follow: Follow | None = rv.scalar_one_or_none()
    assert follow is None

    await session.refresh(user_2, attribute_names=["following_links"])
    assert len(user_2.followed) == 0 # type: ignore

@pytest.mark.asyncio
async def test_pop_followed_no_orphans_left(seed_data, session):
    """
    Разрыв связи user через user.followed[0].pop() должно удалять связанные Follow‑записи
    (и не оставлять орфанов).
    """
    user_2: User | None = await session.get(User, 2)
    assert user_2

    stmt = select(Follow).where(Follow.followee_id == 1)
    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow.id == 1
    assert follow.follower_id == 2
    assert follow.followee_id == 1

    user_2.followed.pop(0) # type: ignore
    await session.flush()

    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow is None

    await session.refresh(user_2, attribute_names=["following_links"])
    assert len(user_2.followed) == 0 # type: ignore


# Проверка Tweet
@pytest.mark.asyncio
async def test_create_tweet(seed_data, session):
    """Добавление через user.tweets.append создаёт твит"""
    user: User | None = await session.get(User, 1)
    new_tweet: Tweet = Tweet(tweet_data="some tweet data")
    user.tweets.append(new_tweet) # type: ignore
    await session.flush()

    stmt = select(Tweet).where(Tweet.author_id == 1)
    rv = await session.execute(stmt)
    user_tweets = rv.all()
    assert len(user_tweets) == 2

# Проверка Like
@pytest.mark.asyncio
async def test_like_by_append(seed_data, session):
    """Создание лайка с помощью user.liked_tweets.append(tweet)"""
    user: User = User(name="new_username")
    session.add(user)
    await session.flush()
    await session.refresh(user, ["likes"])
    tweet: Tweet | None = await session.get(Tweet, 1)
    user.liked_tweets.append(tweet)
    await session.flush()
    assert user.likes[0].tweet_id == 1
    assert user.liked_tweets[0].author_id == 1
    assert len(user.liked_tweets[0].liked_users) == 2

@pytest.mark.asyncio
async def test_double_like_exception(seed_data, session):
    """Повторный лайк должен упасть"""
    user: User | None = await session.get(User, 2)
    tweet: Tweet | None = await session.get(Tweet, 1)
    user.liked_tweets.append(tweet)
    with pytest.raises(IntegrityError):
        await session.flush()

# Проверка Media
@pytest.mark.asyncio
async def test_create_media_and_append(seed_data, session):
    """Создание Media"""
    tweet: Tweet | None = await session.get(Tweet, 1)
    new_media: Media = Media(file_ext="jpg", size=54)
    tweet.medias.append(new_media)
    await session.flush()
    media = tweet.medias[0]
    assert media.relative_path == f"/{tweet.id}/{media.uuid}.{media.file_ext}"

@pytest.mark.asyncio
async def test_media_no_parent_exception(seed_data, session):
    """Создание Media без tweet_id должно упасть"""
    new_media: Media = Media(file_ext="jpg", size=54,
                             uuid="81ced630-5502-4c71-92b3-d64931cd24f7")
    session.add(new_media)
    with pytest.raises(IntegrityError):
        await session.flush()


