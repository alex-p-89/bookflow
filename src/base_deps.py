from typing_extensions import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db_session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

TokenDep = Annotated[str, Depends(oauth2_scheme)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


