from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

#-------Base schemas-----------
class BaseSchema(BaseModel):
    result: bool = Field(True, description='Request result')

class ErrorSchema(BaseSchema):
    message: str = Field(default=None, description='Error message')

#-------User schemas-----------
class BaseUser(BaseModel):
    name: str = Field(description='User name')

class UserOut(BaseUser):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="User id")

class UserDetailed(UserOut):
    followers: List[UserOut] = Field(description='Followers list')
    following: List[UserOut] = Field(description='Following users list')

class UserSchema(BaseSchema):
    user: UserDetailed = Field(description='User schema with "user" key')


class UserCreate(BaseUser):
    ...





#-------Tweet schemas-----------
class BaseTweet(BaseSchema):
    tweet_data: str = Field(description="Tweet text content")
    tweet_media_ids: List[int] = Field(description="List of tweet media ids")


class TweetCreate(BaseTweet):
    ...


class Tweet(BaseTweet):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Tweet id")



#-------Media schemas-----------