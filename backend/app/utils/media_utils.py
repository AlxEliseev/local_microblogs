import asyncio
import shutil
import logging
from typing import BinaryIO
import uuid as uuid_lib
from ..config import MEDIA_STORAGE

logger = logging.getLogger(__name__)

async def save_file_to_storage(file: BinaryIO, mime_type: str, user_id: int):
    uuid = uuid_lib.uuid4()
    file_ext = mime_type.split('/')[-1]
    file_name = f'{uuid}.{file_ext}'
    user_dir = MEDIA_STORAGE / str(user_id)
    file_path = user_dir / file_name

    def write_file(file_obj):
        user_dir.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file_obj, f)

    await asyncio.to_thread(write_file, file)

    relative_path = file_path.relative_to(MEDIA_STORAGE)

    return uuid, str(relative_path)