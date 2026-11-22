from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated, Any

from src.base_deps import SessionDep
from src.common_schemas import BookStatus, PaginationLimit, PaginationOffset
from src.dependencies import AuthDep, CurrentUserDep, RedisDep, RepositoryDep
from src.exceptions import CredentialsException, NotEnoughPermissionsException
from src.schemas import (
    AccessTokenSchema,
    BookCreateSchema,
    BookQueryFilter,
    BookResponseSchema,
    BookUpdateSchema,
    UserBookShelfResponseSchema,
    UserRegisterSchema,
    UserResponseSchema,
    UserToBookLinkCreateSchema,
    UserToBookLinkResponseSchema,
    UserToBookLinkUpdateSchema,
)

books_router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"],
)

auth_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authorization"],
)

users_router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)

bookshelf_router = APIRouter(
    prefix="/api/v1/shelf",
    tags=["Bookshelf"],
)


@books_router.post("/", description="Add book", response_model=BookResponseSchema)
async def add_book(
    session: SessionDep,
    repository: RepositoryDep,
    current_user: CurrentUserDep,
    data: BookCreateSchema,
) -> Any:
    result = await repository.add_book(session, data, user_id=current_user.user_id)
    return result


@books_router.get(
    "/", description="Get all books", response_model=List[BookResponseSchema]
)
async def get_books(
    session: SessionDep,
    repository: RepositoryDep,
    *,
    limit: PaginationLimit = 10,
    offset: PaginationOffset = 0,
    filtering: Annotated[BookQueryFilter, Depends()],
) -> List[Any]:
    active_filters = filtering.model_dump(exclude_none=True)

    result = await repository.get_books(
        session, limit=limit, offset=offset, **active_filters
    )
    return result


@books_router.get(
    "/top",
    description="Get top N books by average rating",
    response_model=List[BookResponseSchema],
)
async def get_top_n_books(
    session: SessionDep,
    repository: RepositoryDep,
    redis: RedisDep,
    n: int = 3,
    descending_order: bool = True,
) -> List[BookResponseSchema]:
    result = await repository.get_top_n_books(session, redis, n, descending_order)
    return result


@books_router.get(
    "/{book_id}", description="Get book by ID", response_model=BookResponseSchema
)
async def get_book(session: SessionDep, repository: RepositoryDep, book_id: int) -> Any:
    result = await repository.get_book(session, book_id)
    return result


@books_router.put(
    "/{book_id}", description="Edit book information", response_model=BookResponseSchema
)
async def edit_book(
    session: SessionDep,
    repository: RepositoryDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    book_id: int,
    data: BookUpdateSchema,
) -> Any:
    db_book = await repository.get_book(session, book_id)
    current_user_id = current_user.user_id
    if db_book.owner_id != current_user_id:
        raise NotEnoughPermissionsException(current_user_id)

    result = await repository.edit_book_directly(session, redis, db_book, data)
    return result


@books_router.delete(
    "/{book_id}", description="Delete book by ID", response_model=BookResponseSchema
)
async def delete_book(
    session: SessionDep,
    redis: RedisDep,
    repository: RepositoryDep,
    current_user: CurrentUserDep,
    book_id: int,
) -> Any:
    db_book = await repository.get_book(session, book_id)
    current_user_id = current_user.user_id
    if db_book.owner_id != current_user_id:
        raise NotEnoughPermissionsException(current_user_id)

    result = await repository.delete_book_directly(session, redis, db_book)
    return result


@auth_router.post(
    "/register", description="Register user", response_model=UserResponseSchema
)
async def register_user(
    session: SessionDep, repository: RepositoryDep, data: UserRegisterSchema
) -> Any:
    result = await repository.register_user(session, data)
    return result


@auth_router.post(
    "/login", description="Authorize user", response_model=AccessTokenSchema
)
async def login_user(
    session: SessionDep,
    auth: AuthDep,
    login_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> AccessTokenSchema:
    db_user = await auth.authenticate_user(
        session, login_data.username, login_data.password
    )
    if not db_user:
        raise CredentialsException

    user_data = {"sub": str(db_user.user_id)}
    access_token = auth.generate_access_token(user_data)
    return AccessTokenSchema(access_token=access_token, token_type="bearer")


@users_router.get("/me", description="User profile", response_model=UserResponseSchema)
async def get_me(current_user: CurrentUserDep) -> Any:
    return current_user


@bookshelf_router.post(
    "/",
    description="Add book to bookshelf",
    response_model=UserToBookLinkResponseSchema,
)
async def add_book_to_shelf(
    session: SessionDep,
    repository: RepositoryDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    data: UserToBookLinkCreateSchema,
) -> Any:
    result = await repository.add_book_to_shelf(session, redis, current_user, data)
    return result


@bookshelf_router.post(
    "/{book_id}",
    description="Change book status",
    response_model=UserToBookLinkResponseSchema,
)
async def change_book_status(
    session: SessionDep,
    repository: RepositoryDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    book_id: int,
    new_data: UserToBookLinkUpdateSchema,
) -> Any:
    result = await repository.change_book_status(
        session, redis, current_user.user_id, book_id, new_data
    )
    return result


@bookshelf_router.get(
    "/", description="User bookshelf", response_model=UserBookShelfResponseSchema
)
async def get_user_book_shelf(
    session: SessionDep,
    repository: RepositoryDep,
    current_user: CurrentUserDep,
    book_status_filter: Optional[BookStatus] = None,
) -> Any:
    result = await repository.get_user_book_shelf(
        session, current_user, book_status_filter
    )
    return result
