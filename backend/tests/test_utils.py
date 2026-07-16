import pytest
from pathlib import Path
import io

from ..app.utils.media_utils import save_file_to_storage
from ..app.config import MEDIA_STORAGE, APP_DIR

TESTS_DIR: Path = Path(__file__).resolve().parent


@pytest.mark.asyncio
async def test_file_saving():
    """File should be saved by correct path (app/media/<user_id>/<file_name>)"""
    test_image_path = TESTS_DIR / "medias" / "test_image.jpeg"
    media = io.BytesIO(test_image_path.read_bytes())
    uuid, relative_path = await save_file_to_storage(media, "image/jpeg", 1)
    file_path = MEDIA_STORAGE / relative_path
    file_name = f"{uuid}.jpeg"
    assert Path(file_path) == MEDIA_STORAGE / "1" / file_name
    assert Path(file_path).exists() is True
