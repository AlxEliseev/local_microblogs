from typing import List
import uuid as uuid_lib

from sqlalchemy import ARRAY, Integer, String, UniqueConstraint, ForeignKey, CheckConstraint, Uuid
from sqlalchemy import event, inspect, select, delete, Result
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base, DeclarativeBase
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.asyncio import AsyncSession



class Base(DeclarativeBase):
    def __repr__(self):
        columns = [c.key for c in inspect(self.__class__).columns]
        attrs = {k: getattr(self, k) for k in columns}
        attr_str = ", ".join(f"{k}={v!r}" for k, v in attrs.items())
        return f"{self.__class__.__name__}({attr_str})"

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    follower_links: Mapped[List["Follow"]] = relationship("Follow",
                                                      back_populates="followee",
                                                      foreign_keys="Follow.followee_id",
                                                      lazy="selectin",
                                                      cascade="all, delete-orphan",
                                                      )
    followers: Mapped[List["User"]] = association_proxy("follower_links",
                                                        "follower",
                                                        creator=lambda u: Follow(follower=u))

    following_links: Mapped[List["Follow"]] = relationship("Follow",
                                                     back_populates="follower",
                                                     foreign_keys="Follow.follower_id",
                                                     lazy="selectin",
                                                     cascade="all, delete-orphan",
                                                     )
    following: Mapped[List["User"]] = association_proxy("following_links",
                                                       "followee",
                                                       creator=lambda u: Follow(followee=u)
                                                       )

    likes: Mapped[List["Like"]] = relationship("Like",
                                               back_populates="user",
                                               lazy="selectin",
                                               cascade="all, delete-orphan",
                                               )
    liked_tweets: Mapped[List["Tweet"]] = association_proxy("likes",
                                                      "tweet",
                                                      creator=lambda t: Like(tweet=t)
                                                      )

    tweets: Mapped[List["Tweet"]] = relationship("Tweet",
                                                 back_populates="author",
                                                 lazy="selectin",
                                                 cascade="all, delete-orphan",
                                                 )


class Tweet(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet_data: Mapped[str] = mapped_column(String(500), nullable=False)

    medias: Mapped[List["Media"]] = relationship("Media",
                                                 back_populates="tweet",
                                                 lazy="selectin",
                                                 cascade="all, delete-orphan",
                                                 )
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship("User",
                                          back_populates="tweets",
                                          lazy="joined",
                                          innerjoin=True,
                                          cascade="save-update",
                                          )
    likes: Mapped[List["Like"]] = relationship("Like",
                                               back_populates="tweet",
                                               lazy="selectin",
                                               cascade="all, delete-orphan",
                                               )
    liked_users: Mapped[List["User"]] = association_proxy("likes", "user")


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followee_id"),
                      CheckConstraint("follower_id <> followee_id"), )

    id: Mapped[int] = mapped_column(primary_key=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    followee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    follower: Mapped["User"] = relationship("User",
                                            foreign_keys=[follower_id],
                                            back_populates="following_links",
                                            lazy="joined",
                                            innerjoin=True,
                                            cascade="save-update",
                                            )

    followee: Mapped["User"] = relationship("User",
                                            foreign_keys=[followee_id],
                                            back_populates="follower_links",
                                            lazy="joined",
                                            innerjoin=True,
                                            cascade="save-update",
                                            )


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "tweet_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)

    user: Mapped["User"] = relationship("User",
                                        back_populates="likes",
                                        lazy="joined",
                                        innerjoin=True,
                                        cascade="save-update",
                                        )

    tweet: Mapped["Tweet"] = relationship("Tweet",
                                          back_populates="likes",
                                          lazy="joined",
                                          innerjoin=True,
                                          cascade="save-update",)


class Media(Base):
    __tablename__ = "medias"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    file_ext: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"), nullable=False)
    tweet: Mapped["Tweet"] = relationship("Tweet",
                                          back_populates="medias",
                                          lazy="joined",
                                          innerjoin=True,
                                          cascade="save-update",
                                          )

    relative_path: Mapped[str] = mapped_column(String(255), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "uuid") or self.uuid is None:
            self.uuid = uuid_lib.uuid4()

@event.listens_for(Media, 'before_insert')
def construct_relative_path(mapper, connection, media_obj):
    media_obj.relative_path = f"/{media_obj.tweet_id}/{media_obj.uuid}.{media_obj.file_ext}"

async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    """
    Gets user from database by User.id
    :param user_id: User.id
    :param session: database transaction session
    :return: User object
    """
    stmt = select(User).where(User.id == user_id)
    rv = await session.execute(stmt)
    user: User = rv.scalar_one_or_none()
    return user

async def get_user_by_api_key(api_key: str, session: AsyncSession) -> User:
    """
    Gets user from database with API key secret
    :param api_key: API key for user
    :param session: database transaction session
    :return: User object
    """
    #This function should be changed with ApiKeys model with secrets
    user: User = await get_user_by_id(int(api_key), session) # TODO change for production
    return user

async def follow(follower_id: int, followee_id: int, session: AsyncSession):
    """
    Follow User(id=followee_id) by User(id=follower_id)
    :param follower_id:
    :param followee_id:
    :param session: database transaction session
    """
    follow: Follow = Follow(follower_id=follower_id, followee_id=followee_id)
    session.add(follow)
    await session.flush()

async def unfollow(follower_id: int, followee_id: int, session: AsyncSession):
    stmt = (delete(Follow).
            where(Follow.follower_id == follower_id,
                  Follow.followee_id == followee_id).
            returning(Follow.followee_id))
    rv = await session.execute(stmt)
    return rv.scalar_one_or_none()