import pytest
from pathlib import Path
from fastapi import status
from ..app import exceptions as app_exceptions
from ..app.schemas import ErrorSchema


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/tweets", "/api/users/me", "/api/users/2"])
async def test_route_status(app_client, seed_data, route):
    """Все GET роуты должны вернуть 200"""
    rv = await app_client.get(route, headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_post_follow(app_client, seed_data):
    """POST запрос должен заффоловить другого пользователя"""
    rv = await app_client.post("/api/users/2/follow", headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {"result": True}


@pytest.mark.asyncio
async def test_post_follow_double_follow_exception(app_client, seed_data):
    """Повторный фоллов должен выбросить исключение"""
    rv = await app_client.post("/api/users/1/follow", headers={"api-key": "2"})
    assert rv.json() == {
        "result": False,
        "error_type": "AlreadyFollowingError",
        "error_message": "Already following this user",
    }
    assert rv.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_unfollow(app_client, seed_data):
    """Unfollow пользователя должен вернуть 200"""
    rv = await app_client.delete("/api/users/1/follow", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {"result": True}


@pytest.mark.asyncio
async def test_unfollow_no_follow_exception(app_client, seed_data):
    """Если пытаемся unfollow того, кого не фолловим, должно вернуться 404"""
    rv = await app_client.delete("/api/users/2/follow", headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_404_NOT_FOUND
    assert rv.json() == {
        "result": False,
        "error_type": "NoFollowError",
        "error_message": "No such follow in database",
    }


@pytest.mark.asyncio
async def test_get_me(app_client, seed_data):
    """Должен вывести информацию о текущем пользователе"""
    rv = await app_client.get("/api/users/me", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {
        "result": True,
        "user": {
            "id": 2,
            "name": "user2",
            "followers": [],
            "following": [{"id": 1, "name": "user1"}],
        },
    }


@pytest.mark.asyncio
async def test_get_user(app_client, seed_data):
    """Должен вывести информацию о пользователе по id"""
    rv = await app_client.get("/api/users/1", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {
        "result": True,
        "user": {
            "id": 1,
            "name": "user1",
            "followers": [{"id": 2, "name": "user2"}],
            "following": [],
        },
    }


@pytest.mark.asyncio
async def test_create_media(app_client, seed_data):
    """Tests if media loads correctly"""
    app_dir = Path(__file__).resolve().parent.parent
    test_image_path = app_dir / "tests" / "medias" / "test_image.jpeg"
    with open(test_image_path, "rb") as media_file:
        files = {"file": ("test_image.jpeg", media_file, "image/jpeg")}
        rv = await app_client.post("/api/medias", files=files, headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_201_CREATED
    assert rv.json() == {"result": True, "media_id": 2}


@pytest.mark.asyncio
async def test_create_tweet(app_client, seed_data):
    """Tests if tweet creates correctly"""
    rv = await app_client.post(
        "/api/tweets",
        headers={"api-key": "1"},
        json={"tweet_data": "That is my first test tweet", "tweet_media_ids": [1]},
    )

    assert rv.status_code == status.HTTP_201_CREATED
    assert rv.json() == {"result": True, "tweet_id": 2}


@pytest.mark.asyncio
async def test_create_tweet_media_not_found_exception(app_client, seed_data):
    """If no media exists with id in 'tweet_media_ids' parameter, exception raises"""
    rv = await app_client.post(
        "/api/tweets",
        headers={"api-key": "1"},
        json={"tweet_data": "That is my first test tweet", "tweet_media_ids": [1, 2]},
    )

    assert rv.status_code == status.HTTP_404_NOT_FOUND
    expected_dict = ErrorSchema(
        result=False,
        error_type=app_exceptions.MediaNotFoundError().error_type,
        error_message=app_exceptions.MediaNotFoundError.detail,
    ).model_dump()

    assert rv.json() == expected_dict


@pytest.mark.asyncio
async def test_home_feed(app_client, seed_data):
    """Tests if users list of tweet returns correctly"""
    rv = await app_client.get("/api/tweets", headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {
        "result": True,
        "tweets": [
            {
                "id": 1,
                "content": "Some text data",
                "attachments": [
                    "/api/media/f18d1520-0c80-46af-b4ad-366027e6ad1a",
                ],
                "author": {"id": 1, "name": "user1"},
                "likes": [{"user_id": 2, "name": "user2"}],
            }
        ],
    }


@pytest.mark.asyncio
async def test_delete_tweet(app_client, seed_data):
    """User can delete his own tweet"""
    rv = await app_client.delete("/api/tweets/1", headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {"result": True}


@pytest.mark.asyncio
async def test_delete_tweet_no_permission_exception(app_client, seed_data):
    """If tried to delete another users tweet, exception should be raised"""
    rv = await app_client.delete("/api/tweets/1", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_404_NOT_FOUND
    assert rv.json() == {
        "result": False,
        "error_type": "TweetNotFoundError",
        "error_message": "Tweet not found or access denied",
    }


@pytest.mark.asyncio
async def test_like_tweet(app_client, seed_data):
    """User can like tweet"""
    rv = await app_client.post("/api/tweets/1/likes", headers={"api-key": "1"})
    assert rv.status_code == status.HTTP_201_CREATED
    assert rv.json() == {"result": True}


@pytest.mark.asyncio
async def test_double_like_exception(app_client, seed_data):
    """Exception should be raised if tried to like tweet twice"""
    rv = await app_client.post("/api/tweets/1/likes", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_409_CONFLICT
    assert rv.json() == {
        "result": False,
        "error_type": "DoubleLikeError",
        "error_message": "Already liked this tweet",
    }


@pytest.mark.asyncio
async def test_like_tweet_no_tweet_exception(app_client, seed_data):
    """If tried to like tweet that does not exist, exception raised"""
    rv = await app_client.post("/api/tweets/10/likes", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_404_NOT_FOUND
    assert rv.json() == {
        "result": False,
        "error_type": "TweetNotFoundError",
        "error_message": "Tweet not found or access denied",
    }


@pytest.mark.asyncio
async def test_delete_like(app_client, seed_data):
    """User can delete his own like"""
    rv = await app_client.delete("/api/tweets/1/likes", headers={"api-key": "2"})
    assert rv.status_code == status.HTTP_200_OK
    assert rv.json() == {"result": True}


@pytest.mark.asyncio
async def test_delete_like_no_like_exception(app_client, seed_data):
    """If user didn't like tweet exception should be raised"""
    rv = await app_client.delete("/api/tweets/1/likes", headers={"api-key": "1"})
    assert rv.status_code == app_exceptions.NoLikeError.status_code
    expected_dict = ErrorSchema(
        result=False,
        error_type=app_exceptions.NoLikeError().error_type,
        error_message=app_exceptions.NoLikeError.detail,
    ).model_dump()

    assert rv.json() == expected_dict
