from fastapi import APIRouter, status

from app.api.deps import UserServiceDep
from app.api.v1.schemas import UserRegisterRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: UserRegisterRequest, service: UserServiceDep) -> UserResponse:
    user = await service.register(username=payload.username, password=payload.password)
    return UserResponse.model_validate(user)
