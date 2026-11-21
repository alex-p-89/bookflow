from typing import List, Optional

from redis.asyncio import Redis
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, with_loader_criteria

from src.common_schemas import BookStatus
from src.exceptions import (
    BookNotFoundException,
    BookShelfAddException,
    BookShelfLinkNotFoundException,
    UserExistsException,
)
from src.models import BookModel, UserModel, UserToBookLinkModel
from src.schemas import (
    BookCreateSchema,
    BookResponseSchema,
    BookUpdateSchema,
    UserRegisterSchema,
    UserToBookLinkCreateSchema,
    UserToBookLinkUpdateSchema,
    books_list_adapter,
)
from src.utils import hash_password


class BookFlowRepository:
    @staticmethod
    async def add_book(
        db: AsyncSession, data: BookCreateSchema, user_id: int
    ) -> BookModel:
        db_book = BookModel(**data.model_dump(), owner_id=user_id)
        db.add(db_book)
        await db.commit()
        return db_book

    @staticmethod
    async def get_book(db: AsyncSession, book_id: int) -> BookModel:
        query = select(BookModel).where(BookModel.book_id == book_id)
        db_book = (await db.scalars(query)).first()
        if not db_book:
            raise BookNotFoundException(book_id)
        return db_book

    @staticmethod
    async def get_books(
        db: AsyncSession, limit: Optional[int], offset: Optional[int], **filters: str
    ) -> List[BookModel]:
        query = select(BookModel)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        if filters:
            for key, value in filters.items():
                filter_field = getattr(BookModel, key)
                query = query.where(filter_field == value)

        return list((await db.scalars(query)).all())

    @staticmethod
    async def edit_book(
        db: AsyncSession, book_id: int, new_data: BookUpdateSchema
    ) -> BookModel:
        query = select(BookModel).where(BookModel.book_id == book_id)
        db_book = (await db.scalars(query)).first()
        if not db_book:
            raise BookNotFoundException(book_id)

        for field, value in new_data.model_dump(exclude_unset=True).items():
            setattr(db_book, field, value)

        await db.commit()
        return db_book

    @staticmethod
    async def edit_book_directly(
        db: AsyncSession, db_book: BookModel, new_data: BookUpdateSchema
    ) -> BookModel:
        for field, value in new_data.model_dump(exclude_unset=True).items():
            setattr(db_book, field, value)

        await db.commit()
        return db_book

    @staticmethod
    async def delete_book(db: AsyncSession, book_id: int) -> BookModel:
        query = select(BookModel).where(BookModel.book_id == book_id)
        db_book = (await db.scalars(query)).first()
        if not db_book:
            raise BookNotFoundException(book_id)

        await db.delete(db_book)
        await db.commit()
        return db_book

    @staticmethod
    async def delete_book_directly(db: AsyncSession, db_book: BookModel) -> BookModel:
        await db.delete(db_book)
        await db.commit()
        return db_book

    @staticmethod
    async def register_user(db: AsyncSession, data: UserRegisterSchema) -> UserModel:
        hashed_password = hash_password(data.password)
        db_user = UserModel(
            username=data.username, email=data.email, hashed_password=hashed_password
        )
        db.add(db_user)

        try:
            await db.commit()
        except IntegrityError as ie:
            await db.rollback()
            raise UserExistsException(
                reason=str(ie.orig), username=data.username, email=data.email
            )

        return db_user

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
        query = select(UserModel).where(UserModel.email == email)
        db_user = (await db.scalars(query)).first()
        return db_user

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession, username: str
    ) -> Optional[UserModel]:
        query = select(UserModel).where(UserModel.username == username)
        db_user = (await db.scalars(query)).first()
        return db_user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, id: int) -> Optional[UserModel]:
        query = select(UserModel).where(UserModel.user_id == id)
        db_user = (await db.scalars(query)).first()
        return db_user

    @staticmethod
    async def add_book_to_shelf(
        db: AsyncSession,
        redis: Optional[Redis],
        user: UserModel,
        data: UserToBookLinkCreateSchema,
    ) -> UserToBookLinkModel:
        await db.refresh(user, attribute_names=["book_associations"])

        book = UserToBookLinkModel(**data.model_dump())
        user.book_associations.append(book)
        try:
            await db.commit()
            if redis is not None:
                await BookFlowRepository._inc_top_n_books_key_version(redis)
        except IntegrityError as ie:
            await db.rollback()
            raise BookShelfAddException(str(ie.orig), data.book_id)

        return book

    @staticmethod
    async def change_book_status(
        db: AsyncSession,
        redis: Optional[Redis],
        user_id: int,
        book_id: int,
        new_data: UserToBookLinkUpdateSchema,
    ) -> UserToBookLinkModel:
        query = select(UserToBookLinkModel).where(
            UserToBookLinkModel.user_id == user_id,
            UserToBookLinkModel.book_id == book_id,
        )

        u2b_link = (await db.scalars(query)).first()
        if not u2b_link:
            raise BookShelfLinkNotFoundException(user_id, book_id)

        for field, value in new_data.model_dump(exclude_unset=True).items():
            setattr(u2b_link, field, value)

        await db.commit()
        if redis is not None:
            await BookFlowRepository._inc_top_n_books_key_version(redis)

        return u2b_link

    @staticmethod
    async def get_user_book_shelf(
        db: AsyncSession, user: UserModel, filter_by_status: Optional[BookStatus]
    ) -> UserModel:
        query = (
            select(UserModel)
            .where(UserModel.user_id == user.user_id)
            .options(
                selectinload(UserModel.book_associations).joinedload(
                    UserToBookLinkModel.book
                )
            )
        )
        if filter_by_status:
            query = query.options(
                with_loader_criteria(
                    UserToBookLinkModel, UserToBookLinkModel.status == filter_by_status
                )
            )

        query = query.execution_options(populate_existing=True)

        await db.execute(query)

        return user

    @staticmethod
    async def _get_top_n_books_key_version(redis: Redis) -> int:
        version = await redis.get("top_n_books_version")
        return int(version) if version is not None else 1

    @staticmethod
    async def _inc_top_n_books_key_version(redis: Redis) -> None:
        await redis.incr("top_n_books_version", 1)

    @staticmethod
    async def get_top_n_books(
        db: AsyncSession, redis: Optional[Redis], n: int, descending_order: bool
    ) -> List[BookResponseSchema]:
        if redis is not None:
            cache_key_version = await BookFlowRepository._get_top_n_books_key_version(
                redis
            )
            cache_key = f"top_n_books:v{cache_key_version}"

            cached_data = await redis.get(cache_key)
            if cached_data is not None:
                books_from_cache = books_list_adapter.validate_json(cached_data)
                return books_from_cache

        avg_rating = func.avg(UserToBookLinkModel.rating).label("avg_rating")

        query = (
            select(BookModel, avg_rating)
            .join(UserToBookLinkModel, BookModel.book_id == UserToBookLinkModel.book_id)
            .group_by(BookModel.book_id)
            .order_by(desc(avg_rating) if descending_order else avg_rating)
            .limit(n)
        )

        books = (await db.scalars(query)).all()
        if redis is not None:
            books_schemas = books_list_adapter.validate_python(books)
            books_to_cache = books_list_adapter.dump_json(books_schemas)
            await redis.set(cache_key, books_to_cache, ex=10)

        return list(books)
