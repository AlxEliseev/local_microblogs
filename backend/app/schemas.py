from pydantic import BaseModel, Field, ConfigDict
from typing import List

#-------User schemas-----------
class BaseUser(BaseModel):
    name: str = Field(description='User name')


class UserCreate(BaseUser):
    ...


class User(BaseUser):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="User id")


#-------Tweet schemas-----------
class BaseTweet(BaseModel):
    tweet_data: str = Field(description="Tweet text content")
    tweet_media_ids: List[int] = Field(description="List of tweet media ids")


class TweetCreate(BaseTweet):
    ...


class Tweet(BaseTweet):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Tweet id")



#-------Media schemas-----------