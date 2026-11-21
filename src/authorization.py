from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError

from src.config import settings
from src.repository import BookFlowRepository
from src.models import UserModel
from src.utils import verify_password
from src.base_deps import TokenDep, SessionDep
from src.exceptions import CredentialsException


class AuthorizationModule:
    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        username: str, 
        password: str
    ) -> Optional[UserModel]:
        db_user = await BookFlowRepository.get_user_by_username(session, username)
        if not db_user:
            return None

        hashed_password = db_user.hashed_password
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode("utf-8") 
        if not verify_password(password, hashed_password):
            return None
        
        return db_user

    @staticmethod
    def generate_access_token(
        user_data: Dict[str, Any], 
        expiration_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = user_data.copy()
        if not expiration_delta:
            expiration_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.now(timezone.utc) + expiration_delta
        to_encode.update({"exp": expire})
        token = jwt.encode(
            payload=to_encode, 
            key=settings.SECRET_KEY.get_secret_value(), 
            algorithm=settings.ALGORITHM
        )

        return token

    @staticmethod
    async def get_current_user(
        session: SessionDep,
        access_token: TokenDep
    ) -> UserModel:
        try:
            payload = jwt.decode(
                jwt=access_token, 
                key=settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM],
            )
            sub = payload.get("sub")
            if sub is None:
                raise CredentialsException
            
        except InvalidTokenError:
            raise CredentialsException

        id_from_token = int(sub)
        db_user = await BookFlowRepository.get_user_by_id(session, id_from_token)
        if db_user is None:
            raise CredentialsException
        
        return db_user



