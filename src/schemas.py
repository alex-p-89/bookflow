from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter
from typing_extensions import Annotated

from src.common_schemas import (
    BookRating,
    BookStatus,
    Id,
    LongStr,
    ShortStr,
    Year,
)


class BookQueryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    genre: Annotated[Optional[str], Field(description="Filter by genre")] = None
    author: Annotated[Optional[str], Field(description="Filter by author")] = None


class BookshelfQueryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Annotated[
        Optional[BookStatus], Field(description="Filter by book status")
    ] = None


class BookCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Annotated[ShortStr, Field(description="Book title")]
    author: Annotated[ShortStr, Field(description="Book author")]
    published: Annotated[Year, Field(description="Year of book publication")]
    genre: Annotated[ShortStr, Field(description="Book genre")]
    description: Optional[
        Annotated[LongStr, Field(description="Brief book description")]
    ] = None


class BookUpdateSchema(BookCreateSchema):
    pass


class BookResponseSchema(BookCreateSchema):
    book_id: Annotated[Id, Field(description="Book ID")]
    owner_id: Annotated[Id, Field(description="Owner ID")]


books_list_adapter = TypeAdapter(List[BookResponseSchema])


class UserBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: Annotated[ShortStr, Field(description="Username")]
    email: Annotated[EmailStr, Field(description="e-mail for registration")]


class UserRegisterSchema(UserBaseSchema):
    password: Annotated[ShortStr, Field(description="User password")]


class UserResponseSchema(UserBaseSchema):
    user_id: Annotated[Id, Field(description="User ID")]


class AccessTokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserToBookLinkCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: Annotated[Id, Field(description="Book ID")]
    status: BookStatus
    rating: Optional[BookRating] = None


class UserToBookLinkUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: BookStatus
    rating: Optional[BookRating] = None


class UserToBookLinkResponseSchema(UserToBookLinkCreateSchema):
    user_id: Annotated[Id, Field(description="User ID")]


class UserBookShelfResponseSchema(UserResponseSchema):
    books: Annotated[
        List[BookResponseSchema], Field(description="Books from personal bookshelf")
    ]
