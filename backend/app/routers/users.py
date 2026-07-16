from typing import Annotated

from fastapi import APIRouter, Path, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..exceptions import AlreadyFollowingError, NoFollowError, NoUserError
from ..schemas import BaseSchema, ErrorSchema, UserSchema
from ..models import User, Follow
from ..utils.users_utils import check_api_key
from ..utils.logging_utils import router_logging
from ..crud import UserCRUD, FollowCRUD

router = APIRouter(
    prefix="/api/users",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorSchema,
            "description": "Unauthorized",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorSchema, "description": "Not found"},
        status.HTTP_409_CONFLICT: {"model": ErrorSchema, "description": "Conflict"},
    },
    tags=["users"],
)


@router.post(
    "/{id}/follow",
    response_model=BaseSchema,
    summary="Follow user",
    description="Follow user by User.id",
)
@router_logging("POST", "/api/users/{id}/follow")
async def follow_user(
    id: Annotated[int, Path()],
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    try:
        await FollowCRUD(session).follow(follower_id=user.id, followee_id=id)
        await session.flush()
    except IntegrityError:
        raise AlreadyFollowingError
    return {}


@router.delete(
    "/{id}/follow",
    response_model=BaseSchema,
    summary="Unfollow user",
    description="Unfollow user by User.id",
)
@router_logging("DELETE", "/api/users/{id}/follow")
async def unfollow_user(
    id: Annotated[str, Path()],
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    deleted_follow = await FollowCRUD(session).unfollow(
        follower_id=user.id, followee_id=int(id)
    )
    if not deleted_follow:
        raise NoFollowError
    return {}


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Current user information",
    description="Shows current user information with following and followers info",
)
@router_logging("GET", "/api/users/me")
async def get_account_info(
    user: User = Depends(check_api_key), session: AsyncSession = Depends(get_session)
):
    user: User = await UserCRUD(session).get_by_id(
        user.id,
        options=[
            selectinload(User.following_links).selectinload(Follow.followee),
            selectinload(User.follower_links).selectinload(Follow.follower),
        ],
    )
    return {"user": user}


@router.get(
    "/{id}",
    response_model=UserSchema,
    dependencies=[
        Depends(check_api_key),
    ],
    summary="User information",
    description="Shows user information with following and followers info",
)
@router_logging("GET", "/api/users/{id}")
async def get_user_info(
    id: Annotated[int, Path()], session: AsyncSession = Depends(get_session)
):
    user: User = await UserCRUD(session).get_by_id(
        id,
        options=[
            selectinload(User.following_links).selectinload(Follow.followee),
            selectinload(User.follower_links).selectinload(Follow.follower),
        ],
    )
    if not user:
        raise NoUserError
    return {"user": user}
