from typing import List
import uuid as uuid_lib

from sqlalchemy import Integer, String, UniqueConstraint, ForeignKey, CheckConstraint, Uuid
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped, mapped_column, relationship,DeclarativeBase
from sqlalchemy.ext.associationproxy import association_proxy


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
                                                      cascade="all, delete-orphan",
                                                      )
    followers: Mapped[List["User"]] = association_proxy("follower_links",
                                                        "follower",
                                                        creator=lambda u: Follow(follower=u))

    following_links: Mapped[List["Follow"]] = relationship("Follow",
                                                     back_populates="follower",
                                                     foreign_keys="Follow.follower_id",
                                                     cascade="all, delete-orphan",
                                                     )
    following: Mapped[List["User"]] = association_proxy("following_links",
                                                       "followee",
                                                       creator=lambda u: Follow(followee=u)
                                                       )

    likes: Mapped[List["Like"]] = relationship("Like",
                                               back_populates="user",
                                               cascade="all, delete-orphan",
                                               )
    liked_tweets: Mapped[List["Tweet"]] = association_proxy("likes",
                                                      "tweet",
                                                      creator=lambda t: Like(tweet=t)
                                                      )

    tweets: Mapped[List["Tweet"]] = relationship("Tweet",
                                                 back_populates="author",
                                                 cascade="all, delete-orphan",
                                                 )


class Tweet(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet_data: Mapped[str] = mapped_column(String(500), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"),
                                           nullable=False, index=True)

    medias: Mapped[List["Media"]] = relationship("Media",
                                                 back_populates="tweet",
                                                 cascade="all, delete-orphan",
                                                 )

    author: Mapped["User"] = relationship("User",
                                          back_populates="tweets",
                                          cascade="save-update",
                                          )
    likes: Mapped[List["Like"]] = relationship("Like",
                                               back_populates="tweet",
                                               cascade="all, delete-orphan",
                                               )
    liked_users: Mapped[List["User"]] = association_proxy("likes", "user")


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followee_id",
                                       name="uq_follower_followee"),
                      CheckConstraint("follower_id <> followee_id",
                                      name="chk_no_self_follow"), )

    id: Mapped[int] = mapped_column(primary_key=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                             nullable=False)
    followee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                             nullable=False, index=True)

    follower: Mapped["User"] = relationship("User",
                                            foreign_keys=[follower_id],
                                            back_populates="following_links",
                                            innerjoin=True,
                                            cascade="save-update",
                                            )

    followee: Mapped["User"] = relationship("User",
                                            foreign_keys=[followee_id],
                                            back_populates="follower_links",
                                            innerjoin=True,
                                            cascade="save-update",
                                            )


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "tweet_id",
                                       name="uq_user_tweet_like"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                         nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"),
                                          nullable=False, index=True)

    user: Mapped["User"] = relationship("User",
                                        back_populates="likes",
                                        innerjoin=True,
                                        cascade="save-update",
                                        )

    tweet: Mapped["Tweet"] = relationship("Tweet",
                                          back_populates="likes",
                                          innerjoin=True,
                                          cascade="save-update",)


class Media(Base):
    __tablename__ = "medias"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_lib.UUID] = mapped_column(Uuid, nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="SET NULL"),
                                          nullable=True)

    tweet: Mapped["Tweet"] = relationship("Tweet",
                                          back_populates="medias",
                                          innerjoin=False,
                                          cascade="save-update",
                                          )

    relative_path: Mapped[str] = mapped_column(String(255), nullable=True)