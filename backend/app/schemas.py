from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import List, Optional, Any
from uuid import UUID

#TODO какой то бардак со схемами
#-------Base schemas-----------
class BaseSchema(BaseModel):
    result: bool = Field(True, description='Request result')

class ErrorSchema(BaseSchema):
    error_type: str = Field(default=None, description='Error type')
    error_message: str = Field(default=None, description='Error message')

#-------User schemas-----------
class BaseUser(BaseModel):
    name: str = Field(description='User name')

class UserOut(BaseUser):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="User id")


class UserDetailed(UserOut):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="User id")
    followers: List[UserOut] = Field(description='Followers list')
    following: List[UserOut] = Field(description='Following users list')

class UserSchema(BaseSchema):
    user: UserDetailed = Field(description='User schema with "user" key')


#-------Like schemas-----------
class BaseLike(BaseModel):
    user_id: int = Field(description="User id", validation_alias="id")
    name: str = Field(description='User name')


#-------Media schemas-----------
class MediaSchema(BaseSchema):
    media_id: int = Field(description="Media id")

class MediaLink(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID = Field(description="Уникальный идентификатор медиа")
    @computed_field(description="Временная ссылка на медиафайл")
    @property
    def link(self) -> str:
        return f"/{self.uuid}"

#-------Tweet schemas-----------
class TweetCreate(BaseModel):
    tweet_data: str = Field(description="Tweet text content")
    tweet_media_ids: List[int] = Field(description="List of tweet media ids")


class BaseTweet(BaseSchema):
    tweet_id: int = Field(description="Tweet id")


class TweetDetailed(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Tweet id")
    content: str = Field(description="Tweet text data", validation_alias="tweet_data")
    author: UserOut = Field(description="Author data")
    likes: List[BaseLike] = Field(description="Liked user data", validation_alias="liked_users")
    medias: List[Any] = Field(default_factory=list, repr=False, exclude=True)

    @computed_field(description="Список ссылок на медиафайл")
    @property
    def attachments(self) -> List[str]:
        medias = getattr(self, "medias", []) or []
        links = []
        for media in medias:
            link = f"/api/media/{media.uuid}"
            links.append(link)
        return links


class HomeFeedSchema(BaseSchema):
    tweets: List[TweetDetailed] = Field(description='List of tweets for user')


