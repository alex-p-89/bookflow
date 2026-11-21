from typing import Optional, Type

from fastapi import Depends, Request
from redis.asyncio import Redis
from typing_extensions import Annotated

from src.authorization import AuthorizationModule
from src.models import UserModel
from src.repository import BookFlowRepository


def get_auth_module() -> Type[AuthorizationModule]:
    return AuthorizationModule


async def get_bookflow_repository() -> Type[BookFlowRepository]:
    return BookFlowRepository


async def get_redis(request: Request) -> Optional[Redis]:
    if request.app.state.redis_online is True:
        return request.app.state.redis
    else:
        return None


AuthDep = Annotated[Type[AuthorizationModule], Depends(get_auth_module)]
CurrentUserDep = Annotated[UserModel, Depends(AuthorizationModule.get_current_user)]
RepositoryDep = Annotated[Type[BookFlowRepository], Depends(get_bookflow_repository)]
RedisDep = Annotated[Redis, Depends(get_redis)]
