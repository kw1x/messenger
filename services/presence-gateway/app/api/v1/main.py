from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.ws import router as ws_router
from app.core.config import settings

router = APIRouter(prefix=settings.V1_PREFIX)
router.include_router(ws_router)
router.include_router(health_router)
