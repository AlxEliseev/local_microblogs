from typing import Sequence, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy import select, delete as sql_delete, or_, update as sql_update, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import NoResultFound
from . import models
from .utils.logging_utils import crud_logging


class BaseCRUD[ModelType: models.Base]:
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self, obj_id: int, options: Sequence[ExecutableOption] = None
    ) -> ModelType | None:
        """
        Returns instance of models.Base subclass from database
        :param obj_id: models.Base subclass object id
        :param options: Relationships for lazyload
        :return: models.Base subclass object
        """
        stmt = select(self.model).where(self.model.id == obj_id)
        if options:
            stmt = stmt.options(*options)

        rv = await self.session.execute(stmt)

        if options:
            return rv.unique().scalar_one_or_none()
        return rv.scalar_one_or_none()

    async def get_all_by_ids(self, obj_ids: List[int]) -> List[ModelType]:
        """
        Return list of models.Base subclass object instances from database
        :param obj_ids: list object ids
        :return: List of of models.Base subclass objects
        """
        stmt = select(self.model).where(self.model.id.in_(obj_ids))
        rv = await self.session.execute(stmt)
        return list(rv.scalars().all())

    @crud_logging
    async def create(self, **obj_kwargs) -> ModelType:
        """
        Creates and puts to AsyncSession models.Base subclass instance
        :param obj_kwargs: kwargs of database object
        :return: models.Base subclass object
        """
        new_obj = self.model(**obj_kwargs)
        self.session.add(new_obj)
        return new_obj

    @crud_logging
    async def delete(self, *, obj_id: int, **filters) -> int | None:
        """
        Deletes object (models.Base subclass instance) from database
        :param obj_id: models.Base subclass object id
        :param filters: additional parameters to check before deleting
        :return: deleted object id if success, otherwise returns None
        """

        stmt = (
            sql_delete(self.model)
            .where(self.model.id == obj_id)
            .returning(self.model.id)
        )

        for f_key, f_value in filters.items():
            column = getattr(self.model, f_key, None)
            if column is not None:
                stmt = stmt.where(column == f_value)

        rv = await self.session.execute(stmt)
        return rv.scalar_one_or_none()

    @crud_logging
    async def update(self, *, obj_id: int, **columns) -> ModelType | None:
        """
        Updates models.Base subclass object parameters
        :param obj_id: models.Base subclass object id
        :param columns: parameters with values to update
        :return: updated object
        """
        valid_values = {}
        for c_key, c_value in columns.items():
            column = getattr(self.model, c_key, None)
            if column is not None:
                valid_values[c_key] = c_value

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

    async def get_user_by_api_key(self, api_key: str) -> models.User | None:
        """
        Gets user from database with API key secret
        :param api_key: API key for user
        :return: User object
        """
        # This function should be changed with ApiKeys model with secrets
        if api_key == "test":
            api_key = 1

        try:
            api_key = int(api_key)
        except ValueError:
            return None
        user: models.User = await self.get_by_id(
            int(api_key)
        )  # TODO change for production

        return user


class FollowCRUD(BaseCRUD[models.Follow]):
    model = models.Follow

    @crud_logging
    async def follow(self, *, follower_id: int, followee_id: int) -> models.Follow:
        """
        Follow user by another user. Creates models.Follow object and puts it to the session
        :param follower_id: Follower id (models.User.id)
        :param followee_id: Following user id (models.User.id)
        :return: models.Follow object
        """
        new_follow: models.Follow = models.Follow(
            follower_id=follower_id, followee_id=followee_id
        )
        self.session.add(new_follow)
        return new_follow

    @crud_logging
    async def unfollow(self, *, follower_id: int, followee_id: int) -> int | None:
        """
        Unfollow previously followed user. Deletes models.Follow object
        :param follower_id: Follower id (models.User.id)
        :param followee_id: Following user id (models.User.id)
        :return: deleted models.Follow.user_id if success, otherwise returns None
        """
        stmt = (
            sql_delete(self.model)
            .where(
                self.model.follower_id == follower_id,
                self.model.followee_id == followee_id,
            )
            .returning(self.model.followee_id)
        )
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
        following_ids_stmt = select(models.Follow.followee_id).where(
            models.Follow.follower_id == user_id
        )

        liked_tweet_ids_stmt = select(models.Like.tweet_id).where(
            models.Like.user_id == user_id
        )

        stmt = (
            select(models.Tweet)
            .outerjoin(models.Like)
            .where(
                or_(
                    # models.Tweet.author_id == user_id, # user tweets
                    models.Tweet.author_id.in_(following_ids_stmt), # following tweets
                    # models.Tweet.id.in_(liked_tweet_ids_stmt), # liked tweets
                )
            )
            .group_by(models.Tweet.id)
            .order_by(func.count(models.Like.id).desc()) # desc order by likes count
            .options(
                selectinload(models.Tweet.medias),
                selectinload(models.Tweet.author),
                selectinload(models.Tweet.likes).selectinload(models.Like.user),
            )
        )

        rv = await self.session.execute(stmt)
        return rv.scalars().all()


class LikeCRUD(BaseCRUD[models.Like]):
    model = models.Like

    @crud_logging
    async def like(self, *, user_id: int, tweet_id: int) -> models.Like:
        """
        Likes tweet. Creating models.Like object and puts it ti the session
        :param user_id: Liking user id
        :param tweet_id: tweet id
        :return: models.Like object if success
        """
        new_like: models.Like = models.Like(user_id=user_id, tweet_id=tweet_id)
        self.session.add(new_like)
        return new_like

    @crud_logging
    async def unlike(self, *, user_id: int, tweet_id: int) -> int | None:
        """
        Unlikes previously liked tweet. Deletes models.Like object
        :param user_id: liked user id (models.Like.user_id)
        :param tweet_id: liked tweet id (models.Like.tweet_id)
        :return: id of deleted models.Like if success, None otherwise
        """
        stmt = (
            sql_delete(models.Like)
            .where(models.Like.user_id == user_id, models.Like.tweet_id == tweet_id)
            .returning(models.Like.id)
        )
        rv = await self.session.execute(stmt)
        deleted_like_id = rv.scalar_one_or_none()
        return deleted_like_id
