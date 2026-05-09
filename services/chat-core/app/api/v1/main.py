from fastapi import APIRouter

from app.api.v1.views import auth, chats, messages, users
from app.core.config import settings

router = APIRouter(prefix=settings.V1_PREFIX)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(chats.router)
router.include_router(messages.router)
