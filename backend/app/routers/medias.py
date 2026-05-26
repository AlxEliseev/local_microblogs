from fastapi import APIRouter


router = APIRouter(
    prefix="/api/medias",
    tags=["medias"]
)

@router.post("")
def load_media():
    ...