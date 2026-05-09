from fastapi import APIRouter, Request, Response, status
from redis.asyncio import Redis

router = APIRouter(tags=["meta"])


@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", include_in_schema=False)
async def readyz(request: Request, response: Response) -> dict[str, str]:
    """Liveness vs readiness — readyz fails closed if Redis is unreachable."""
    redis: Redis = request.app.state.redis
    try:
        await redis.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "redis_unavailable"}
    return {"status": "ready"}
