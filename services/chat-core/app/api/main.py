from fastapi import APIRouter

from app.api.v1.main import router as v1_router
from app.core.config import settings

router = APIRouter(prefix=settings.API_PREFIX)
router.include_router(v1_router)
