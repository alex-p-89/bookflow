from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

db_engine = create_async_engine(settings.DATABASE_URL)


class ModelBase(DeclarativeBase):
    pass


new_session = async_sessionmaker(db_engine, expire_on_commit=False)


async def get_db_session():
    async with new_session() as session:
        yield session
