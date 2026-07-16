from typing import Annotated
from fastapi import APIRouter, Path, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..database import get_session
from ..exceptions import (
    MediaNotFoundError,
    TweetNotFoundError,
    DoubleLikeError,
    ApplicationException,
    NoLikeError,
)
from ..schemas import BaseSchema, ErrorSchema, TweetCreate, HomeFeedSchema, BaseTweet
from ..models import User, Tweet
from ..utils.users_utils import check_api_key
from ..utils.logging_utils import router_logging
from ..crud import TweetCRUD, LikeCRUD, MediaCRUD

router = APIRouter(
    prefix="/api/tweets",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorSchema,
            "description": "Unauthorized",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema, "description": "Not found"},
        status.HTTP_409_CONFLICT: {"model": ErrorSchema, "description": "Conflict"},
    },
    tags=["tweets"],
)


@router.post(
    "",
    response_model=BaseTweet,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorSchema,
            "description": "Media not found",
        },
    },
    status_code=status.HTTP_201_CREATED,
    summary="Create new tweet",
    description="Posts new tweet with tweet_data and medias",
)
@router_logging("POST", "/api/tweets")
async def create_new_tweet(
    tweet_data: TweetCreate,
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):

    tweet_data_dict = tweet_data.model_dump()
    media_ids = tweet_data_dict["tweet_media_ids"]
    tweet_dict = {
        "author_id": user.id,
        "tweet_data": tweet_data_dict["tweet_data"],
        "medias": [],
    }

    new_tweet: Tweet = await TweetCRUD(session).create(**tweet_dict)
    all_tweet_medias = await MediaCRUD(session).get_all_by_ids(media_ids)
    new_tweet.medias = all_tweet_medias

    if len(media_ids) > len(all_tweet_medias):
        raise MediaNotFoundError

    await session.flush()
    return {"tweet_id": new_tweet.id}


@router.delete(
    "/{id}",
    response_model=BaseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorSchema,
            "description": "Tweet not found",
        }
    },
    status_code=status.HTTP_200_OK,
    summary="Delete tweet",
    description="Deletes users tweet by Tweet.id",
)
@router_logging("DELETE", "/api/tweets/{id}")
async def delete_tweet(
    id: Annotated[int, Path()],
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    deleted_tweet_id = await TweetCRUD(session).delete(obj_id=id, author_id=user.id)
    if not deleted_tweet_id:
        raise TweetNotFoundError
    return {}


@router.post(
    "/{id}/likes",
    response_model=BaseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorSchema,
            "description": "Tweet not found",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorSchema,
            "description": "Like already exists",
        },
    },
    status_code=status.HTTP_201_CREATED,
    summary="Likes tweet",
    description="Likes tweet by Tweet.id",
)
@router_logging("POST", "/api/tweets/{id}/likes")
async def post_like(
    tweet_id: Annotated[int, Path(alias="id")],
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    try:
        await LikeCRUD(session).like(user_id=user.id, tweet_id=tweet_id)
        await session.flush()
    except IntegrityError as exc:
        pg_codes = {"23503": TweetNotFoundError, "23505": DoubleLikeError}
        error = pg_codes.get(getattr(exc.orig, "sqlstate", None))
        if error:
            raise error
        else:
            raise ApplicationException
    return {}


@router.delete(
    "/{id}/likes",
    response_model=BaseSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorSchema,
            "description": "Like does not exist",
        }
    },
    status_code=status.HTTP_200_OK,
    summary="Deletes like",
    description="Deletes tweet like by Tweet.id",
)
@router_logging("DELETE", "/api/tweets/{id}/likes")
async def delete_like(
    tweet_id: Annotated[int, Path(alias="id")],
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    deleted_like_id = await LikeCRUD(session).unlike(user_id=user.id, tweet_id=tweet_id)
    if not deleted_like_id:
        raise NoLikeError
    return {}


@router.get(
    "",
    response_model=HomeFeedSchema,
    status_code=status.HTTP_200_OK,
    summary="Get users home feed",
    description="Return tweets for users home feed",
)
@router_logging("GET", "/api/tweets")
async def get_home_feed(
    user: User = Depends(check_api_key), session: AsyncSession = Depends(get_session)
):
    tweets_for_user = await TweetCRUD(session).get_feed(user.id)
    return {"tweets": tweets_for_user}
