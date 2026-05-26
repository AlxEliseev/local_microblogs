from fastapi import APIRouter


router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

@router.post("/<id>/follow")
def follow_user():
    ...

@router.delete("/<id>/follow")
def unfollow_user():
    ...

@router.get("/me")
def get_account_info():
    ...

@router.get("/<id>")
def get_user_info():
    ...