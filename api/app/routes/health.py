from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.config import settings
from app.db import SessionFactory
from app.schemas import HealthRead

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthRead)
async def health() -> HealthRead:
    return HealthRead(application="ok", environment=settings.app_env)


@router.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with SessionFactory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"application": "ok", "database": "ok"}
