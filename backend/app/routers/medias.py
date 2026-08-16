from typing import Annotated
from fastapi import APIRouter, File, UploadFile, Depends, Path, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import ErrorSchema, MediaSchema
from ..utils.media_utils import save_file_to_storage
from ..utils.users_utils import check_api_key
from ..utils.logging_utils import router_logging
from ..crud import MediaCRUD
from ..config import MEDIA_STORAGE

router = APIRouter(
    prefix="/api",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorSchema,
            "description": "Unauthorized",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorSchema,
            "description": "Media not found",
        },
    },
    tags=["medias"],
)


@router.post(
    "/medias",
    response_model=MediaSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Send media",
    description="Sends media to server and saves",
)
@router_logging("POST", "/api/medias")
async def load_media(
    media_file: UploadFile = File(..., alias="file"),
    user: User = Depends(check_api_key),
    session: AsyncSession = Depends(get_session),
):
    mime_type = media_file.content_type
    file_uuid, relative_path = await save_file_to_storage(
        media_file.file, mime_type, user.id
    )
    media_params = {
        "uuid": file_uuid,
        "mime_type": mime_type,
        "size": media_file.size,
        "relative_path": relative_path,
    }

    new_media = await MediaCRUD(session).create(**media_params)
    await session.flush()
    if file_uuid and relative_path and new_media.id:
        return {"media_id": new_media.id}


@router.get(
    "/media/{uuid}",
    summary="Get media",
    description="Get media from server",
)
@router_logging("GET", "/api/medias/{uuid}")
async def get_media(
    uuid: Annotated[str, Path()], session: AsyncSession = Depends(get_session)
):
    media = await MediaCRUD(session).get_media_by_uuid(uuid)
    file_path = MEDIA_STORAGE / media.relative_path
    return FileResponse(path=file_path, media_type=media.mime_type)
