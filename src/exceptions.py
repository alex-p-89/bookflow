from typing import Union

from fastapi import HTTPException, status


class BookNotFoundException(HTTPException):
    def __init__(self, book_id: int):
        detail = f"Book with ID={book_id} does not exist"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class FilterByFieldException(HTTPException):
    def __init__(self, filter_by: str):
        detail = (
            f"Filtering by the field {filter_by} is not allowed, "
            f"or the field does not exist"
        )

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class UserExistsException(HTTPException):
    def __init__(self, *, reason: str, username: str, email: str):
        if "username" in reason:
            detail = (
                f"User with name {username} is already registered"
            )
        elif "email" in reason:
            detail = (
                f"User with email {email} is already registered"
            )
        else:
            detail = (
                "Unknown registration error"
            )

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class UserNotFoundException(HTTPException):
    def __init__(self, search_field: Union[str, int]):
        if isinstance(search_field, str):
            detail = (
                f"User with email {search_field} does not exist"
            )
        elif isinstance(search_field, int):
            detail = (
                f"User with ID={search_field} does not exist"
            )
        else:
            detail = (
                "User does not exit"
            )

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class CredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization error",
            headers={"WWW-Authenticate": "Bearer"},
        )

class NotEnoughPermissionsException(HTTPException):
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with ID={user_id} "
                   f"does not have permission to modify the object"
        )

class BookShelfAddException(HTTPException):
    def __init__(self, reason: str, book_id: int):
        if "unique" in reason.lower():
            detail = (
                f"Book with ID={book_id} is already added to the bookshelf"
            )
        elif "foreign" in reason.lower():
            detail = (
                f"Book with ID={book_id} does not exist"
            )
        else:
            detail = (
                "Error adding to bookshelf"
            )

        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class BookShelfLinkNotFoundException(HTTPException):
    def __init__(self, user_id: int, book_id: int):
        detail = (
            f"User with ID={user_id} has not added "
            f"book with ID={book_id} to bookshelf"
        )

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )