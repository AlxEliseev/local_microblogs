from fastapi import HTTPException, status


class ApplicationException(HTTPException):
    # TODO Что если сделать общий ApplicationException(Exception)
    # и в глобальном обработчике превращать его в HTTPException
    # и полностью отделить слои crud, FastApi routes
    # ошибки лучше ловить в crud
    """Base exceptions class"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Application error occurred"

    def __init__(self, detail: str = None, status_code: int = None):
        # if details did not pass, return default details
        current_code = status_code or self.status_code
        current_detail = detail or self.detail
        super().__init__(status_code=current_code, detail=current_detail)

    @property
    def error_type(self) -> str:
        """Error type is a name of exception class"""
        return self.__class__.__name__


class AuthorizationError(ApplicationException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "No API key passed"


class NoUserError(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No such user in database"


class AlreadyFollowingError(ApplicationException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Already following this user"


class NoFollowError(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No such follow in database"


class MediaNotFoundError(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Media with this ID does not exist"


class TweetNotFoundError(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Tweet not found or access denied"


class DoubleLikeError(ApplicationException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Already liked this tweet"


class NoLikeError(ApplicationException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No like in database"
