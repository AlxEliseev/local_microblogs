from typing import Annotated, List
from fastapi import APIRouter, Path, Depends, Body

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from ..database import get_session
from ..exceptions import (MediaNotFoundError,
                          TweetNotFoundError,
                          DoubleLikeError,
                          ApplicationException,
                          NoLikeError)
from ..schemas import BaseSchema, ErrorSchema, TweetCreate, HomeFeedSchema, BaseTweet
from ..models import User, Tweet
from ..utils.users_utils import check_api_key
from ..crud import TweetCRUD, LikeCRUD, MediaCRUD


router = APIRouter(
    prefix="/api/tweets",
    responses={401: {"model": ErrorSchema, "description": "Unauthorized"},
               404: {"model": ErrorSchema, "description": "Not found"},
               409: {"model": ErrorSchema, "description": "Conflict"}},
    tags=["tweets"]
)

@router.post("",
             response_model=BaseTweet,
             responses={
                 404: {"model": ErrorSchema, "description": "Media not found"},
             },
             status_code=201,
             summary='Create new tweet',
             description='Posts new tweet with tweet_data and medias'
             )
async def create_new_tweet(tweet_data: TweetCreate,
                           user: User = Depends(check_api_key),
                           session: AsyncSession = Depends(get_session)):

    tweet_data_dict = tweet_data.model_dump()
    data = tweet_data_dict['tweet_data']
    media_ids = tweet_data_dict['tweet_media_ids']
    tweet_dict = {'author_id': user.id,
                  'tweet_data': data,
                  'medias': []}

    new_tweet: Tweet = await TweetCRUD(session).create(**tweet_dict)
    all_tweet_medias = await MediaCRUD(session).get_all_by_ids(media_ids)
    new_tweet.medias = all_tweet_medias

    if len(media_ids) > len(all_tweet_medias):
        raise MediaNotFoundError

    await session.flush()
    return {'tweet_id': new_tweet.id}


@router.delete("/{id}",
               response_model=BaseSchema,
               responses={
                   404: {"model": ErrorSchema, "description": "Tweet not found"}
               },
               status_code=200,
               summary='Delete tweet',
               description='Deletes users tweet by Tweet.id'
               )
async def delete_tweet(id:Annotated[int, Path()],
                       user: User = Depends(check_api_key),
                       session: AsyncSession = Depends(get_session)
                       ):
    deleted_tweet_id = await TweetCRUD(session).delete(id, author_id=user.id)
    if not deleted_tweet_id:
        raise TweetNotFoundError
    return {}


@router.post("/{id}/likes",
             response_model = BaseSchema,
             responses = {
                 404: {"model": ErrorSchema, "description": "Tweet not found"},
                 409: {"model": ErrorSchema, "description": "Like already exists"}
             },
             status_code = 201,
             summary = 'Likes tweet',
             description = 'Likes tweet by Tweet.id'
             )
async def post_like(tweet_id:Annotated[int, Path(alias='id')],
                    user: User = Depends(check_api_key),
                    session: AsyncSession = Depends(get_session)):
    try:
        await LikeCRUD(session).like(user.id, tweet_id)
        await session.flush()
    except IntegrityError as exc:
        pg_code = getattr(exc.orig, "sqlstate", None)
        if pg_code == "23503":
            raise TweetNotFoundError
        elif pg_code == "23505":
            raise DoubleLikeError
        else:
            raise ApplicationException
    return {}


@router.delete("/{id}/likes",
             response_model = BaseSchema,
             responses = {
                 404: {"model": ErrorSchema, "description": "Like does not exist"}
             },
             status_code = 200,
             summary = 'Deletes like',
             description = 'Deletes tweet like by Tweet.id'
             )
async def delete_like(tweet_id:Annotated[int, Path(alias='id')],
                      user: User = Depends(check_api_key),
                      session: AsyncSession = Depends(get_session)):
    deleted_like_id = await LikeCRUD(session).unlike(user_id=user.id, tweet_id=tweet_id)
    if not deleted_like_id:
        raise NoLikeError
    return {}

@router.get("",
            response_model=HomeFeedSchema,
            status_code=200,
            summary='Get users home feed',
            description='Return tweets for users home feed'
            )
async def get_home_feed(user: User = Depends(check_api_key),
                        session: AsyncSession = Depends(get_session)):
    tweets_for_user = await TweetCRUD(session).get_feed(user.id)
    return {'tweets': tweets_for_user}