from typing import Annotated

from fastapi import Depends, Header
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..exceptions import AuthorizationError
from ..models import User
from ..crud import UserCRUD


async def check_api_key(
    api_key: Annotated[str | None, Header(alias="api-key")] = None,
    session: AsyncSession = Depends(get_session),
) -> User:

    if not api_key:
        raise AuthorizationError
    user: User = await UserCRUD(session).get_user_by_api_key(api_key)

    if not user:
        raise AuthorizationError(detail=f"Wrong or expired API key")
    return user
