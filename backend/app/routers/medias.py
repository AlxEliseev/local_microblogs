import logging
from typing import Annotated
from fastapi import APIRouter, UploadFile, Depends, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..models import User
from ..schemas import ErrorSchema, MediaSchema
from ..utils.media_utils import save_file_to_storage
from ..utils.users_utils import check_api_key
from ..crud import MediaCRUD
from ..config import MEDIA_STORAGE

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    responses={401: {"model": ErrorSchema, "description": "Unauthorized"},
               404: {"model": ErrorSchema, "description": "Media not found"}},
    tags=["medias"]
)

@router.post("/medias",
             response_model=MediaSchema,
             status_code=201,
             summary='Send media',
             description='Sends media to server and saves')
async def load_media(file: UploadFile,
                     user: User = Depends(check_api_key),
                     session: AsyncSession = Depends(get_session)):
    mime_type = file.content_type
    size = file.size
    file_uuid, relative_path = await save_file_to_storage(file.file, mime_type, user.id)
    media_params = {"uuid": file_uuid,
                    "mime_type": mime_type,
                    "size": size,
                    "relative_path": relative_path}

    new_media = await MediaCRUD(session).create(**media_params)
    await session.flush()
    if file_uuid and relative_path and new_media.id:
        return {'media_id': new_media.id}


@router.get("/media/{uuid}",
             # dependencies=[Depends(check_api_key), ],
             summary='Get media',
             description='Get media from server')
async def get_media(uuid: Annotated[str, Path()],
                    session: AsyncSession = Depends(get_session)):
    media = await MediaCRUD(session).get_media_by_uuid(uuid)
    file_path = MEDIA_STORAGE / media.relative_path
    logger.info(f'Sending file from {file_path}')
    return FileResponse(
        path=file_path,
        media_type=media.mime_type
    )