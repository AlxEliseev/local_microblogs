from typing import Annotated

from fastapi import APIRouter, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from ..database import get_session
from ..exceptions import AlreadyFollowingError, NoFollowError, NoUserError

from ..schemas import BaseSchema, ErrorSchema, UserSchema
from ..models import User, Follow
from ..utils.users_utils import check_api_key
from ..crud import UserCRUD, FollowCRUD

router = APIRouter(
    prefix="/api/users",
    responses={401: {"model": ErrorSchema, "description": "Unauthorized"},
               404: {"model": ErrorSchema, "description": "Not found"},
               409: {"model": ErrorSchema, "description": "Conflict"}},
    tags=["users"]
)


@router.post("/{id}/follow",
             response_model=BaseSchema,
             summary='Follow user',
             description='Follow user by User.id')
async def follow_user(id: Annotated[str, Path()],
                      user: User = Depends(check_api_key),
                      session: AsyncSession = Depends(get_session)):
    try:
        await FollowCRUD(session).follow(follower_id=user.id, followee_id=int(id))
        await session.flush()
    except IntegrityError:
        raise AlreadyFollowingError

    return {}


@router.delete("/{id}/follow",
             response_model=BaseSchema,
             summary='Unfollow user',
             description='Unfollow user by User.id')
async def unfollow_user(id: Annotated[str, Path()],
                        user: User = Depends(check_api_key),
                        session: AsyncSession = Depends(get_session)):
    result = await FollowCRUD(session).unfollow(follower_id=user.id, followee_id=int(id))
    if not result:
        raise NoFollowError
    return {}


@router.get("/me",
            response_model=UserSchema,
            summary='Current user information',
            description='Shows current user information with following and followers info')
async def get_account_info(user: User = Depends(check_api_key),
                           session: AsyncSession = Depends(get_session)):
    user: User = await (UserCRUD(session)
                        .get_by_id(user.id,
                                   options=[selectinload(User.following_links).
                                            selectinload(Follow.followee),
                                            selectinload(User.follower_links).
                                            selectinload(Follow.follower)]))
    return {"user": user}


@router.get("/{id}",
            response_model=UserSchema,
            dependencies=[Depends(check_api_key), ],
            summary='User information',
            description='Shows user information with following and followers info'
            )
async def get_user_info(id: Annotated[int, Path()],
                        session: AsyncSession = Depends(get_session)):
    user: User = await (UserCRUD(session)
                        .get_by_id(id,
                                   options=[selectinload(User.following_links)
                                            .selectinload(Follow.followee),
                                            selectinload(User.follower_links)
                                            .selectinload(Follow.follower)]))
    if not user:
        raise NoUserError
    return {"user": user}

