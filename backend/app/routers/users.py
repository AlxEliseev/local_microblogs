from typing import AsyncGenerator, Annotated

from fastapi import APIRouter, Path, Depends, Header
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..database import get_session

from ..schemas import BaseSchema, ErrorSchema, UserSchema
from ..models import User, get_user_by_api_key, get_user_by_id, follow, unfollow

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

async def check_api_key(api_key: Annotated[str | None, Header(alias="api-key")] = None,
                        session: AsyncSession = Depends(get_session)) -> User:
    if not api_key:
        raise HTTPException(status_code=401, detail="No API key passed")
    user: User = await get_user_by_api_key(api_key, session)
    if not user:
        raise HTTPException(status_code=408, detail=f"Wrong API key {api_key}")
    return user

@router.post("/{id}/follow",
             response_model=BaseSchema,
             responses={
                 401: {"model": ErrorSchema},
                 409: {"model": ErrorSchema},
             },
             summary='Follow user',
             description='Follow user by User.id')
async def follow_user(id: Annotated[str, Path()],
                      user: User = Depends(check_api_key),
                      session: AsyncSession = Depends(get_session)):
    try:
        await follow(follower_id=user.id, followee_id=int(id), session=session)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Already following this user")
    await session.commit()
    return {"result": True}

@router.delete("/{id}/follow",
             response_model=BaseSchema,
             responses={
                 401: {"model": ErrorSchema},
                 404: {"model": ErrorSchema},
             },
             summary='Unfollow user',
             description='Unfollow user by User.id')
async def unfollow_user(id: Annotated[str, Path()],
                        user: User = Depends(check_api_key),
                        session: AsyncSession = Depends(get_session)):
    result = await unfollow(follower_id=user.id, followee_id=int(id), session=session)
    if result:
        return {"result": result}
    else:
        raise HTTPException(status_code=404, detail="No such follow in database")


@router.get("/me",
            response_model=UserSchema,
            responses={
                401: {"model": ErrorSchema}
            },
            summary='Current user information',
            description='Shows current user information with following and followers info')
async def get_account_info(user: User = Depends(check_api_key)):
    return {"user": user}

@router.get("/{id}",
            dependencies=[Depends(check_api_key),],
            response_model=UserSchema,
            responses={
                401: {"model": ErrorSchema},
                404: {"model": ErrorSchema}
            },
            summary='User information',
            description='Shows user information with following and followers info'
            )
async def get_user_info(id: int,
                        session: AsyncSession = Depends(get_session)):
    user: User = await get_user_by_id(id, session)
    if user:
        return {"user": user}
    else:
        raise HTTPException(status_code=404, detail="No such user in database")

