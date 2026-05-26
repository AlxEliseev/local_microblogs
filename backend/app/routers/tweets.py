from fastapi import APIRouter


router = APIRouter(
    prefix="/api/tweets",
    tags=["tweets"]
)

@router.post("")
def create_new_tweet():
    ...

@router.delete("/<id>")
def load_media():
    ...

@router.post("/<id>/likes")
def post_like():
    ...

@router.delete("/<id>/likes")
def delete_like():
    ...

@router.get("")
def get_tweets():
    ...