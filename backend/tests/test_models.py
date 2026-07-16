import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
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
async def test_follow_no_fk_exception(seed_data, session):
    new_follow: Follow = Follow(follower_id=1)
    session.add(new_follow)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_wrong_followee_exception(seed_data, session):
    """Попытка создать Follow с несуществующим followee должна упасть"""
    follow: Follow = Follow(follower_id=1, followee_id=5)
    session.add(follow)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_append_following_creates_follow(seed_data, session):
    """
    Добавление через association_proxy: user.following.append(other)
    должно создавать Follow (проверка creator)
    """
    select_follower_stmt = (
        select(User).where(User.id == 1).options(selectinload(User.following_links))
    )
    select_following_stmt = (
        select(User).where(User.id == 2).options(selectinload(User.follower_links))
    )

    follower = (await session.execute(select_follower_stmt)).scalar_one_or_none()
    following = (await session.execute(select_following_stmt)).scalar_one_or_none()
    assert follower and following

    follower.following.append(following)
    await session.flush()

    stmt = select(Follow).where(Follow.followee_id == 2)
    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow.id == 2
    assert follow.follower_id == 1
    assert follow.followee_id == 2

    assert following.followers[0].id == 1


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
    select_following_stmt = (
        select(User).where(User.id == 1).options(selectinload(User.follower_links))
    )
    select_follower_stmt = (
        select(User).where(User.id == 2).options(selectinload(User.following_links))
    )

    following = (await session.execute(select_following_stmt)).scalar_one_or_none()
    follower = (await session.execute(select_follower_stmt)).scalar_one_or_none()

    assert following.following[0].id == 1

    stmt = select(Follow).where(Follow.followee_id == 1)
    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow.follower_id == 2
    assert follow.followee_id == 1
    await session.delete(following)
    await session.flush()

    rv = await session.execute(stmt)
    follow: Follow | None = rv.scalar_one_or_none()
    assert follow is None

    await session.refresh(follower, attribute_names=["following_links"])
    assert len(user_2.following) == 0  # type: ignore


@pytest.mark.asyncio
async def test_pop_following_no_orphans_left(seed_data, session):
    """
    Разрыв связи user через user.following[0].pop() должно удалять связанные Follow‑записи
    (и не оставлять орфанов).
    """
    stmt = select(User).where(User.id == 2).options(selectinload(User.following_links))
    user = (await session.execute(stmt)).scalar_one_or_none()
    assert user

    stmt = (
        select(Follow)
        .where(Follow.followee_id == 1)
        .options(joinedload(Follow.follower), joinedload(Follow.followee))
    )
    follow: Follow = (await session.execute(stmt)).scalar_one_or_none()

    assert follow.follower_id == 2
    assert follow.followee_id == 1

    user.following.pop(0)  # type: ignore
    await session.flush()

    rv = await session.execute(stmt)
    follow: Follow = rv.scalar_one_or_none()
    assert follow is None

    await session.refresh(user, attribute_names=["following_links"])
    assert len(user.following) == 0  # type: ignore


# Проверка Tweet
@pytest.mark.asyncio
async def test_create_tweet_by_append(seed_data, session):
    """Добавление через user.tweets.append создаёт твит"""
    stmt = select(User).where(User.id == 1).options(selectinload(User.tweets))
    user = (await session.execute(stmt)).scalar_one_or_none()
    new_tweet: Tweet = Tweet(tweet_data="some tweet data")
    user.tweets.append(new_tweet)  # type: ignore
    await session.flush()

    stmt = select(Tweet).where(Tweet.author_id == 1)
    rv = await session.execute(stmt)
    user_tweets = rv.all()
    assert len(user_tweets) == 2


@pytest.mark.asyncio
async def test_create_tweet_by_author(seed_data, session):
    """Добавление через author_id помещает твит в коллекцию user.tweets"""
    stmt = select(User).where(User.id == 2).options(selectinload(User.tweets))
    user = (await session.execute(stmt)).scalar_one_or_none()
    new_tweet: Tweet = Tweet(tweet_data="some tweet data", author=user)
    session.add(new_tweet)
    await session.flush()
    assert user.tweets[0] is new_tweet


@pytest.mark.asyncio
async def test_tweet_params_links_correct(seed_data, session):
    """твит корректно связан с автором, лайкнувшими пользователями"""
    stmt = (
        select(Tweet)
        .where(Tweet.id == 1)
        .options(
            joinedload(Tweet.author, innerjoin=True),
            selectinload(Tweet.likes).joinedload(Like.user),
        )
    )
    tweet: Tweet = (await session.execute(stmt)).scalar_one_or_none()
    assert tweet.author.id == 1
    assert tweet.liked_users[0].id == 2


@pytest.mark.asyncio
async def test_tweet_create_no_author_exception(seed_data, session):
    """Нельзя создать Tweet без author_id, так как поле nullable=False."""
    tweet: Tweet = Tweet(tweet_data="more data")
    session.add(tweet)
    with pytest.raises(IntegrityError):
        await session.flush()


# Проверка Like
@pytest.mark.asyncio
async def test_like_by_append(seed_data, session):
    """Создание лайка с помощью user.liked_tweets.append(tweet)"""
    user: User = User(name="new_username")
    session.add(user)
    await session.flush()
    stmt_tweet = (
        select(Tweet)
        .where(Tweet.id == 1)
        .options(
            joinedload(Tweet.author), selectinload(Tweet.likes).joinedload(Like.user)
        )
    )
    tweet: Tweet = (await session.execute(stmt_tweet)).scalar_one_or_none()
    stmt_user = (
        select(User)
        .where(User.id == user.id)
        .options(selectinload(User.likes).joinedload(Like.tweet))
    )
    user = (await session.execute(stmt_user)).scalar_one()
    user.liked_tweets.append(tweet)
    await session.flush()
    assert user.likes[0].tweet_id == 1
    assert user.liked_tweets[0].author_id == 1
    assert len(user.liked_tweets[0].liked_users) == 2


@pytest.mark.asyncio
async def test_create_like_by_tweet(seed_data, session):
    """
    при создании Like(user=user, tweet=tweet) связь появляется у user.likes,
    через association возвращаются лайкнутые твиты
    """
    new_user: User = User(name="user_3")
    new_like: Like = Like(user=new_user, tweet_id=1)
    session.add_all([new_user, new_like])
    await session.flush()
    await session.refresh(
        new_user,
        [
            "likes",
        ],
    )
    await session.refresh(
        new_like,
        [
            "tweet",
        ],
    )
    assert new_user.likes[0] is new_like
    assert new_user.liked_tweets[0].id == 1


@pytest.mark.asyncio
async def test_doubled_like_exception(seed_data, session):
    """Нельзя создать дубликат лайка для одной пары user_id/tweet_id."""
    new_like = Like(user_id=2, tweet_id=1)
    session.add(new_like)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_like_no_fk_exception(seed_data, session):
    """Нельзя создать лайк без user_id или без tweet_id."""
    new_tweet: Tweet = Tweet(tweet_data="some new test tweet data", author_id=2)
    session.add(new_tweet)
    await session.flush()
    new_like = Like(tweet_id=2)
    session.add(new_like)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_double_like_exception(seed_data, session):
    """Повторный лайк должен упасть"""
    stmt_user = select(User).where(User.id == 2).options(selectinload(User.likes))
    user: User = (await session.execute(stmt_user)).scalar_one_or_none()
    tweet: Tweet | None = await session.get(Tweet, 1)
    user.liked_tweets.append(tweet)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_like_delete_orphan(seed_data, session):
    stmt_user = select(User).where(User.id == 2).options(selectinload(User.likes))
    user: User = (await session.execute(stmt_user)).scalar_one_or_none()
    like = user.likes[0]
    like_id = like.id
    user.likes.pop(0)
    await session.flush()
    stmt = select(Like).where(Like.id == like_id)
    rv = await session.execute(stmt)
    user_like = rv.scalar_one_or_none()
    assert user_like is None


# Проверка Media
@pytest.mark.asyncio
async def test_create_media_and_append(seed_data, session):
    """Создание Media"""
    stmt_tweet = select(Tweet).where(Tweet.id == 1).options(selectinload(Tweet.medias))
    tweet: Tweet = (await session.execute(stmt_tweet)).scalar_one_or_none()
    new_media: Media = Media(
        uuid="f18d1521-0c80-46af-b4ad-366027e6ad1a",
        mime_type="image/jpeg",
        size=100,
        relative_path="relative_path",
    )
    tweet.medias.append(new_media)
    await session.flush()
    media = tweet.medias[1]

    assert media.id == 2
