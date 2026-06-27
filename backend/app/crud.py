from typing import Sequence, List
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy import select, delete as sql_delete, or_, update as sql_update
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import NoResultFound
from . import models

logger = logging.getLogger(__name__)

class BaseCRUD[ModelType: models.Base]:
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self,
                        obj_id: int,
                        options: Sequence[ExecutableOption] = None) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == obj_id)
        if options:
            stmt = stmt.options(*options)

        rv = await self.session.execute(stmt)

        if options:
            return rv.unique().scalar_one_or_none()
        return rv.scalar_one_or_none()

    async def get_all_by_ids(self,
                             obj_ids: list) -> List[ModelType]:
        stmt = select(self.model).where(self.model.id.in_(obj_ids))
        rv = await self.session.execute(stmt)
        return list(rv.scalars().all())

    async def create(self, **obj_kwargs) -> ModelType:
        new_obj = self.model(**obj_kwargs)
        self.session.add(new_obj)
        return new_obj

    async def delete(self, obj_id: int, **filters) -> int | None:
        logger.info(f'Deleting {self.model} object id {obj_id} where {filters}')
        stmt = (sql_delete(self.model).
                where(self.model.id == obj_id).
                returning(self.model.id))

        for key, value in filters.items():
            column = getattr(self.model, key, None)
            if column is not None:
                stmt = stmt.where(column == value)

        rv = await self.session.execute(stmt)
        return rv.scalar_one_or_none()


    async def update(self, obj_id: int, **columns) -> ModelType | None:
        valid_values = {
            key: value
            for key, value in columns.items()
            for column in [getattr(self.model, key, None)]
            if column is not None
        }

        stmt = (
            sql_update(self.model)
            .where(self.model.id == obj_id)
            .values(valid_values)
            .returning(self.model)
        )

        rv = await self.session.execute(stmt)
        return rv.scalar_one_or_none()


class UserCRUD(BaseCRUD[models.User]):
    model = models.User

    async def get_user_by_api_key(self, api_key: str) -> models.User:
        """
        Gets user from database with API key secret
        :param api_key: API key for user
        :return: User object
        """
        # This function should be changed with ApiKeys model with secrets
        if api_key == "test":
            api_key = 1
        user: models.User = await self.get_by_id(int(api_key))  # TODO change for production

        return user


class FollowCRUD(BaseCRUD[models.Follow]):
    model = models.Follow

    async def follow(self, follower_id: int, followee_id:int) -> models.Follow:
        new_follow: models.Follow = models.Follow(follower_id=follower_id,
                                                  followee_id=followee_id)
        self.session.add(new_follow)
        return new_follow

    async def unfollow(self, follower_id: int, followee_id: int) -> int | None:
        stmt = (sql_delete(self.model).
                where(self.model.follower_id == follower_id,
                      self.model.followee_id == followee_id).
                returning(self.model.followee_id))
        rv = await self.session.execute(stmt)
        return rv.scalar_one_or_none()


class MediaCRUD(BaseCRUD[models.Media]):
    model = models.Media

    async def get_media_by_uuid(self, uuid: str) -> models.Media:
        """
        Returns Media instance by its UUID
        :param uuid: Media.uuid parameter
        :return: Media instance
        """
        stmt = select(self.model).filter(self.model.uuid == uuid)
        rv = await self.session.execute(stmt)
        media = rv.scalar_one_or_none()
        if media:
            return media
        else:
            raise NoResultFound(f"Media with UUID {uuid} not found")


class TweetCRUD(BaseCRUD[models.Tweet]):
    model = models.Tweet

    async def get_feed(self, user_id: int) -> Sequence[models.Tweet]:
        """
        Returns tweets feed for user
        :param user_id: users id
        :return: list of tweets for user
        """
        following_ids_stmt = (
            select(models.Follow.followee_id)
            .where(models.Follow.follower_id == user_id)
        )

        liked_tweet_ids_stmt = (
            select(models.Like.tweet_id)
            .where(models.Like.user_id == user_id)
        )

        stmt = (
            select(models.Tweet)
            .where(
                or_(
                    models.Tweet.author_id == user_id,
                    models.Tweet.author_id.in_(following_ids_stmt),
                    models.Tweet.id.in_(liked_tweet_ids_stmt)
                )
            )
            .order_by(models.Tweet.id.desc())
            .distinct()
            .options(selectinload(models.Tweet.medias),
                     selectinload(models.Tweet.author),
                     selectinload(models.Tweet.likes).selectinload(models.Like.user))
        )

        result = await self.session.execute(stmt)
        tweets = result.scalars().all()
        return tweets


class LikeCRUD(BaseCRUD[models.Like]):
    model = models.Like

    async def like(self, user_id: int, tweet_id: int) -> models.Like:
        new_like: models.Like = models.Like(user_id=user_id, tweet_id=tweet_id)
        self.session.add(new_like)
        return new_like

    async def unlike(self, user_id: int, tweet_id: int) -> int:
        stmt = (sql_delete(models.Like)
                .where(models.Like.user_id==user_id,
                       models.Like.tweet_id==tweet_id)
                .returning(models.Like.id))
        rv = await self.session.execute(stmt)
        deleted_like_id = rv.scalar_one_or_none()
        return deleted_like_id
