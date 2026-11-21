from typing import Optional, List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from src.database import ModelBase
from src.common_schemas import BookStatus, BookRating


class BookModel(ModelBase):
    __tablename__ = "books"

    book_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str]
    published: Mapped[int]
    genre: Mapped[str]
    description: Mapped[Optional[str]]
    owner_id: Mapped[int]

    user_associations: Mapped[List["UserToBookLinkModel"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )

class UserModel(ModelBase):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]

    book_associations: Mapped[List["UserToBookLinkModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    books: AssociationProxy[List["BookModel"]] = association_proxy(
        target_collection="book_associations", 
        attr="book",
    )

class UserToBookLinkModel(ModelBase):
    __tablename__ = "users_book_shelf"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.book_id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[BookStatus]
    rating: Mapped[Optional[BookRating]]
    user: Mapped["UserModel"] = relationship(back_populates="book_associations")
    book: Mapped["BookModel"] = relationship(back_populates="user_associations")

